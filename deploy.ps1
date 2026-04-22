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
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 2
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

        $backOk = Test-HttpReady "http://localhost:8000/health"
        $dataOk = Test-HttpReady "http://localhost:8081/health"
        $frontOk = Test-HttpReady "http://localhost:3000/"

        if ($backOk -and $dataOk -and $frontOk) {
            return $true
        }

        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Start-LocalMode {
    Write-Host "Starting Nabu in local mode (no Docker)..." -ForegroundColor Green

    if (-not (Test-Path (Join-Path $script:Root ".env"))) {
        Write-Host "Error: .env file not found at project root." -ForegroundColor Red
        Write-Host "Create it from env.example and set OPENAI_API_KEY." -ForegroundColor Yellow
        exit 1
    }
    if (-not (Test-CommandExists "npm")) {
        Write-Host "Error: npm is not available in PATH." -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path (Join-Path $script:Root ".venv/Scripts/python.exe"))) {
        Write-Host "Error: Python virtual env not found at .venv/Scripts/python.exe" -ForegroundColor Red
        exit 1
    }

    $pythonExe = Join-Path $script:Root ".venv/Scripts/python.exe"

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
