function Stop-Local {
    Write-Host "`n🛑 Stopping local services..." -ForegroundColor Yellow
    
    # Find and kill only uvicorn and dash processes
    Get-Process | Where-Object { $_.ProcessName -match 'python|uvicorn' } | Stop-Process -Force
    
    Write-Host "✅ Services stopped." -ForegroundColor Green
    Start-Sleep -Seconds 2
}
