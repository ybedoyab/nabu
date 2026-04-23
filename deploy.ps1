param(
    [switch]$Docker,
    [switch]$Local
)

$script:Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:Jobs = @()
$script:EndedJobs = @{}

function Test-CommandExists {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Ensure-WingetPackage {
    param(
        [string]$PackageId,
        [string]$DisplayName
    )

    if (-not (Test-CommandExists "winget")) {
        Write-Host "Error: $DisplayName is missing and winget is not available to install it automatically." -ForegroundColor Red
        return $false
    }

    Write-Host "$DisplayName is missing. Installing with winget..." -ForegroundColor Yellow
    try {
        winget install --id $PackageId --silent --accept-package-agreements --accept-source-agreements
        return $true
    } catch {
        Write-Host "Error installing $DisplayName with winget: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Ensure-EnvFile {
    $envPath = Join-Path $script:Root ".env"
    if (Test-Path $envPath) {
        return
    }

    $envExamplePath = Join-Path $script:Root "env.example"
    if (Test-Path $envExamplePath) {
        Copy-Item -Path $envExamplePath -Destination $envPath -Force
        Write-Host "Created .env from env.example. Review OPENAI_API_KEY before using AI features." -ForegroundColor Yellow
        return
    }

    New-Item -Path $envPath -ItemType File -Force | Out-Null
    Write-Host "Created empty .env file. Set OPENAI_API_KEY before using AI features." -ForegroundColor Yellow
}

function Ensure-NodeAndNpm {
    if (Test-CommandExists "npm") {
        return $true
    }

    $installed = Ensure-WingetPackage -PackageId "OpenJS.NodeJS.LTS" -DisplayName "Node.js (npm)"
    if (-not $installed) {
        return $false
    }

    if (-not (Test-CommandExists "npm")) {
        Write-Host "npm is still not available in PATH. Restart the terminal and run deploy.ps1 again." -ForegroundColor Red
        return $false
    }

    return $true
}

function Ensure-PythonBase {
    if ((Test-CommandExists "python") -or (Test-CommandExists "py")) {
        return $true
    }

    $installed = Ensure-WingetPackage -PackageId "Python.Python.3.12" -DisplayName "Python 3.12"
    if (-not $installed) {
        return $false
    }

    if (-not ((Test-CommandExists "python") -or (Test-CommandExists "py"))) {
        Write-Host "Python is still not available in PATH. Restart the terminal and run deploy.ps1 again." -ForegroundColor Red
        return $false
    }

    return $true
}

function New-ProjectVenvIfMissing {
    $venvPython = Join-Path $script:Root ".venv/Scripts/python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
    if (Test-CommandExists "py") {
        & py -3 -m venv (Join-Path $script:Root ".venv")
    } elseif (Test-CommandExists "python") {
        & python -m venv (Join-Path $script:Root ".venv")
    } else {
        Write-Host "Error: Could not find a Python launcher to create .venv." -ForegroundColor Red
        return $null
    }

    if (-not (Test-Path $venvPython)) {
        Write-Host "Error: failed creating .venv at $venvPython" -ForegroundColor Red
        return $null
    }

    return $venvPython
}

function Ensure-PythonDependencies {
    param(
        [string]$PythonExe
    )

    $requirementsPath = Join-Path $script:Root "requirements.txt"
    if (-not (Test-Path $requirementsPath)) {
        Write-Host "Error: requirements.txt not found at project root." -ForegroundColor Red
        return $false
    }

    $hashFile = Join-Path $script:Root ".venv/.nabu-requirements.hash"
    $requirementsHash = (Get-FileHash -Path $requirementsPath -Algorithm SHA256).Hash
    $currentHash = ""
    if (Test-Path $hashFile) {
        $currentHash = (Get-Content $hashFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    }

    if ($requirementsHash -eq $currentHash) {
        return $true
    }

    Write-Host "Installing/updating Python dependencies..." -ForegroundColor Cyan
    & $PythonExe -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { return $false }
    & $PythonExe -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) { return $false }

    Set-Content -Path $hashFile -Value $requirementsHash -Encoding UTF8
    return $true
}

function Ensure-FrontendDependencies {
    $frontendDir = Join-Path $script:Root "frontend"
    $lockFile = Join-Path $frontendDir "package-lock.json"
    $hashFile = Join-Path $frontendDir "node_modules/.nabu-package-lock.hash"

    if (-not (Test-Path $lockFile)) {
        Write-Host "Error: frontend/package-lock.json not found." -ForegroundColor Red
        return $false
    }

    $lockHash = (Get-FileHash -Path $lockFile -Algorithm SHA256).Hash
    $currentHash = ""
    if (Test-Path $hashFile) {
        $currentHash = (Get-Content $hashFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    }

    if ((Test-Path (Join-Path $frontendDir "node_modules")) -and $lockHash -eq $currentHash) {
        return $true
    }

    Write-Host "Installing/updating frontend dependencies..." -ForegroundColor Cyan
    Push-Location $frontendDir
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { return $false }
    } finally {
        Pop-Location
    }

    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        return $false
    }

    Set-Content -Path $hashFile -Value $lockHash -Encoding UTF8
    return $true
}

function Ensure-LocalEnvironment {
    Ensure-EnvFile

    if (-not (Ensure-NodeAndNpm)) {
        return $null
    }

    if (-not (Ensure-PythonBase)) {
        return $null
    }

    $pythonExe = New-ProjectVenvIfMissing
    if (-not $pythonExe) {
        return $null
    }

    if (-not (Ensure-PythonDependencies -PythonExe $pythonExe)) {
        Write-Host "Error: failed installing Python dependencies." -ForegroundColor Red
        return $null
    }

    if (-not (Ensure-FrontendDependencies)) {
        Write-Host "Error: failed installing frontend dependencies." -ForegroundColor Red
        return $null
    }

    return $pythonExe
}

function Stop-LocalJobs {
    if ($script:Jobs.Count -eq 0) {
        return
    }
    foreach ($job in $script:Jobs) {
        if ($job.State -eq "Running") {
            Stop-Job -Job $job -ErrorAction SilentlyContinue | Out-Null
        }
        Remove-Job -Job $job -ErrorAction SilentlyContinue | Out-Null
    }
    $script:Jobs = @()
    $script:EndedJobs = @{}
}

function Stop-ProcessesOnPorts {
    param(
        [int[]]$Ports
    )

    foreach ($port in $Ports) {
        $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $connections) {
            continue
        }

        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            if ($procId -eq $PID) {
                continue
            }
            try {
                $process = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($null -eq $process) {
                    continue
                }
                Write-Host "Port $port is in use by PID $procId ($($process.ProcessName)). Stopping process..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            } catch {
                Write-Host "Warning: Could not stop process PID $procId on port ${port}: $($_.Exception.Message)" -ForegroundColor DarkYellow
            }
        }
    }
}

function Start-TaggedJob {
    param(
        [string]$Name,
        [string]$Tag,
        [string]$WorkingDirectory,
        [string]$Executable,
        [string[]]$Arguments
    )

    $job = Start-Job -Name $Name -ScriptBlock {
        param($Tag, $WorkingDirectory, $Executable, $Arguments)
        Set-Location $WorkingDirectory
        & $Executable @Arguments 2>&1 | ForEach-Object {
            "$Tag $_"
        }
    } -ArgumentList $Tag, $WorkingDirectory, $Executable, $Arguments

    $script:Jobs += $job
}

function Write-TaggedLine {
    param([string]$Line)

    if ($Line.StartsWith("[FRONT]")) {
        Write-Host $Line -ForegroundColor Magenta
    } elseif ($Line.StartsWith("[BACK]")) {
        Write-Host $Line -ForegroundColor Cyan
    } elseif ($Line.StartsWith("[DATA]")) {
        Write-Host $Line -ForegroundColor Yellow
    } else {
        Write-Host $Line
    }
}

function Flush-JobOutput {
    foreach ($job in @($script:Jobs)) {
        Receive-Job -Job $job -ErrorAction SilentlyContinue | ForEach-Object { Write-TaggedLine $_ }
        if ($job.State -in @("Failed", "Stopped", "Completed") -and -not $script:EndedJobs.ContainsKey($job.Id)) {
            $script:EndedJobs[$job.Id] = $true
            Write-Host "[$($job.Name.ToUpper())] process ended with state: $($job.State)" -ForegroundColor Red
        }
    }
}

function Test-HttpReady {
    param(
        [string]$Url
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 2 -UseBasicParsing
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Wait-ForAllServices {
    param([int]$TimeoutSeconds = 120)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Flush-JobOutput

        foreach ($job in @($script:Jobs)) {
            if ($job.State -in @("Failed", "Stopped", "Completed")) {
                return $false
            }
        }

        $backOk = Test-HttpReady "http://127.0.0.1:8000/health"
        $dataOk = Test-HttpReady "http://127.0.0.1:8081/health"
        $frontOk = Test-HttpReady "http://127.0.0.1:3000/"

        if ($backOk -and $dataOk -and $frontOk) {
            return $true
        }

        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Start-LocalMode {
    Write-Host "Starting Nabu in local mode (no Docker)..." -ForegroundColor Green

    $pythonExe = Ensure-LocalEnvironment
    if (-not $pythonExe) {
        exit 1
    }

    Write-Host "Checking required ports (8000, 8081, 3000)..." -ForegroundColor Cyan
    Stop-ProcessesOnPorts -Ports @(8000, 8081, 3000)

    Start-TaggedJob `
        -Name "nabu-back" `
        -Tag "[BACK]" `
        -WorkingDirectory (Join-Path $script:Root "backend") `
        -Executable $pythonExe `
        -Arguments @("-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload")

    Start-TaggedJob `
        -Name "nabu-data" `
        -Tag "[DATA]" `
        -WorkingDirectory (Join-Path $script:Root "data") `
        -Executable $pythonExe `
        -Arguments @("-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8081", "--reload")

    Start-TaggedJob `
        -Name "nabu-front" `
        -Tag "[FRONT]" `
        -WorkingDirectory (Join-Path $script:Root "frontend") `
        -Executable "npm" `
        -Arguments @("run", "dev", "--", "--host", "0.0.0.0", "--port", "3000", "--strictPort")

    Write-Host ""
    Write-Host "Launching services and waiting for readiness..." -ForegroundColor Cyan
    $ready = Wait-ForAllServices -TimeoutSeconds 120
    if (-not $ready) {
        Write-Host "Services did not become ready in time. Check logs above." -ForegroundColor Red
        Stop-LocalJobs
        exit 1
    }

    Write-Host ""
    Write-Host "All services are up:" -ForegroundColor Green
    Write-Host "- Frontend: http://localhost:3000"
    Write-Host "- Backend API: http://localhost:8000"
    Write-Host "- Backend docs: http://localhost:8000/docs"
    Write-Host "- Data API: http://localhost:8081"
    Write-Host "- Data health: http://localhost:8081/health"
    Write-Host ""
    Write-Host "Streaming categorized logs. Press Ctrl+C to stop all." -ForegroundColor Yellow
    Write-Host "Colors: [FRONT]=Magenta, [BACK]=Cyan, [DATA]=Yellow"
    Write-Host ""

    try {
        while ($true) {
            Flush-JobOutput
            Start-Sleep -Milliseconds 250
        }
    } finally {
        Stop-LocalJobs
    }
}

function Start-DockerMode {
    Write-Host "Starting Nabu with Docker Compose..." -ForegroundColor Green
    try {
        docker compose version | Out-Null
    } catch {
        Write-Host "Error: Docker Compose is not available." -ForegroundColor Red
        exit 1
    }

    Set-Location $script:Root
    docker compose up --build
    exit $LASTEXITCODE
}

# Support GNU-style flags from PowerShell invocation
if ($args -contains "--docker") { $Docker = $true }
if ($args -contains "--local") { $Local = $true }

# Default behavior: local mode unless docker explicitly requested
if ($Docker) {
    Start-DockerMode
} else {
    Start-LocalMode
}
