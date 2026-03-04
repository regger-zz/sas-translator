param(
    [string]$SERVER = "root@46.225.121.134",
    [string]$SERVER_PATH = "/root/sas-translator"
    )

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
