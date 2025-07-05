# Manual Azure App Service Restart
# Use this if environment variables aren't active after 10+ minutes

$APP_NAME = "ai-learning-tracker-bharath"
$RESOURCE_GROUP = "AI_Learning_Tracker"

Write-Host "🔄 Manually restarting Azure App Service..." -ForegroundColor Yellow
Write-Host "This ensures environment variables take effect immediately." -ForegroundColor Cyan

# Restart the app service
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Azure App Service restarted successfully!" -ForegroundColor Green
    Write-Host "⏳ Please wait 2-3 minutes for the app to fully restart..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🧪 Test your environment variables:" -ForegroundColor Cyan
    Write-Host "   python test_env_variables.py" -ForegroundColor White
    Write-Host ""
    Write-Host "🌐 Production URL: https://$APP_NAME.azurewebsites.net" -ForegroundColor Cyan
} else {
    Write-Host "❌ Failed to restart Azure App Service" -ForegroundColor Red
    Write-Host "💡 Try restarting manually in Azure Portal:" -ForegroundColor Yellow
    Write-Host "   1. Go to https://portal.azure.com" -ForegroundColor White
    Write-Host "   2. Navigate to App Services > $APP_NAME" -ForegroundColor White
    Write-Host "   3. Click 'Restart' button" -ForegroundColor White
}
