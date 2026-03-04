#!/usr/bin/env pwsh
<#
.SYNOPSIS
    SAS Translator Tool - Manage local development and cloud deployment
.DESCRIPTION
    Unified menu for all SAS Translator operations
.EXAMPLE
    .\sas-tool.ps1
    .\sas-tool.ps1 local
    .\sas-tool.ps1 deploy
#>

param(
    [string]$Command = "menu"
)

# Configuration
$PROJECT_ROOT = "C:\projects\sas_translator"
$BACKEND_DIR = "$PROJECT_ROOT\backend"
$FRONTEND_DIR = "$PROJECT_ROOT\frontend"
$BACKEND_ENV = "sas-backend-env"
$FRONTEND_ENV = "sas-frontend-new"
$SERVER = "root@46.225.121.134"
$SERVER_PATH = "/root/sas-translator"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Show-Menu {
    Clear-Host
    Write-Host @"
╔════════════════════════════════════════════════════════════╗
║           SAS TRANSLATOR - COMMAND CENTER                  ║
╠════════════════════════════════════════════════════════════╣
║  [1] Start Local Development                               ║
║  [2] Stop Local Services                                   ║
║  [3] Deploy to Hetzner                                     ║
║  [4] View Logs (Hetzner)                                   ║
║  [5] Run Tests                                             ║
║  [6] Open Project in VS Code                               ║
║  [7] Exit                                                   ║
╚════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan
}

function Start-Local {
    Write-Host "`n🚀 Starting local development..." -ForegroundColor Green
    
    # Start backend
    Write-Host "Starting backend..." -ForegroundColor Yellow
    $backend = Start-Process -NoNewWindow -FilePath "cmd" -ArgumentList "/k cd $BACKEND_DIR && conda activate $BACKEND_ENV && uvicorn main:app --reload --port 8000" -PassThru
    Start-Sleep -Seconds 3
    
    # Start frontend
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    $frontend = Start-Process -NoNewWindow -FilePath "cmd" -ArgumentList "/k cd $FRONTEND_DIR && conda activate $FRONTEND_ENV && python dash_app.py" -PassThru
    
    Write-Host "`n✅ Services started!" -ForegroundColor Green
    Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   Frontend: http://localhost:8050" -ForegroundColor Cyan
    Write-Host "`nPress any key to return to menu..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

function Stop-Local {
    Write-Host "`n🛑 Stopping local services..." -ForegroundColor Yellow
    taskkill /F /IM python.exe 2>$null
    Write-Host "✅ Services stopped." -ForegroundColor Green
    Start-Sleep -Seconds 2
}

function Deploy-Hetzner {
    Write-Host "`n☁️ Deploying to Hetzner..." -ForegroundColor Green
    
    # Confirm deployment
    $confirm = Read-Host "Deploy to production? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "Deployment cancelled." -ForegroundColor Yellow
        return
    }
    
    # Deploy via SSH
    ssh $SERVER @"
cd $SERVER_PATH
echo "📦 Pulling latest code..."
git pull
echo "🐳 Rebuilding containers..."
docker-compose down
docker-compose up -d --build
echo "📊 Container status:"
docker-compose ps
"@
    
    Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
    Write-Host "   Site: https://sas-translator.com" -ForegroundColor Cyan
    Write-Host "`nPress any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

function View-Logs {
    Write-Host "`n📋 Viewing Hetzner logs (Ctrl+C to exit)..." -ForegroundColor Green
    ssh $SERVER "cd $SERVER_PATH; docker-compose logs -f"
}

function Run-Tests {
    Write-Host "`n🧪 Running tests..." -ForegroundColor Green
    Write-Host "Test suite coming soon!" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

function Open-VSCode {
    Write-Host "`n📝 Opening project in VS Code..." -ForegroundColor Green
    code $PROJECT_ROOT
}

# ============================================================================
# MAIN
# ============================================================================

# Handle direct commands
switch ($Command) {
    "local"  { Start-Local; exit }
    "stop"   { Stop-Local; exit }
    "deploy" { Deploy-Hetzner; exit }
    "logs"   { View-Logs; exit }
    "test"   { Run-Tests; exit }
    "code"   { Open-VSCode; exit }
}

# Interactive menu
do {
    Show-Menu
    $choice = Read-Host "`nEnter your choice"
    
    switch ($choice) {
        "1" { Start-Local }
        "2" { Stop-Local }
        "3" { Deploy-Hetzner }
        "4" { View-Logs }
        "5" { Run-Tests }
        "6" { Open-VSCode }
        "7" { 
            Write-Host "Goodbye! 👋" -ForegroundColor Cyan
            exit 
        }
        default { 
            Write-Host "Invalid choice. Press any key..." -ForegroundColor Red
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
    }
} while ($true)
