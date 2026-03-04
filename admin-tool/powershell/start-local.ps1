param(
    [switch]$NoBackend,
    [switch]$NoFrontend
)

$PROJECT_ROOT = "C:\projects\sas_translator"
$BACKEND_DIR = "$PROJECT_ROOT\backend"
$FRONTEND_DIR = "$PROJECT_ROOT\frontend"
$BACKEND_ENV = "sas-backend-env"
$FRONTEND_ENV = "sas-frontend-new"

Write-Host "`n🚀 Starting local development..." -ForegroundColor Green

if (-not $NoBackend) {
    Write-Host "Starting backend..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -FilePath "cmd" -ArgumentList "/k cd $BACKEND_DIR && conda activate $BACKEND_ENV && uvicorn main:app --reload --port 8000"
    Start-Sleep -Seconds 3
}

if (-not $NoFrontend) {
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -FilePath "cmd" -ArgumentList "/k cd $FRONTEND_DIR && conda activate $FRONTEND_ENV && python dash_app.py"
}

Write-Host "`n✅ Services started!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:8050" -ForegroundColor Cyan