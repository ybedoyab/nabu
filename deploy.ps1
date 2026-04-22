param(
    [switch]$Local
)

if (-not $Local) {
    Write-Host "Cloud deployment is deferred for now." -ForegroundColor Yellow
    Write-Host "Use: .\deploy.ps1 --local" -ForegroundColor Yellow
    exit 0
}

Write-Host "Starting Nabu locally..." -ForegroundColor Green

if (-not (Test-Path ".env")) {
    Write-Host "Error: .env file not found at project root." -ForegroundColor Red
    Write-Host "Create it from env.example and set OPENAI_API_KEY." -ForegroundColor Yellow
    exit 1
}

try {
    docker compose version | Out-Null
} catch {
    Write-Host "Error: Docker Compose is not available." -ForegroundColor Red
    exit 1
}

Write-Host "Building and starting all local services..." -ForegroundColor Blue
docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start local services." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Services started:" -ForegroundColor Cyan
docker compose ps
Write-Host ""
Write-Host "Local URLs:" -ForegroundColor Cyan
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "- Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "- Backend docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "- Data API: http://localhost:8081" -ForegroundColor White
Write-Host "- Data health: http://localhost:8081/health" -ForegroundColor White