# Set Production Environment in Azure
# This ensures proper security settings without affecting costs

$APP_NAME = "ai-learning-tracker-bharath"
$RESOURCE_GROUP = "AI_Learning_Tracker"

Write-Host "🛡️  Setting FLASK_ENV to production for security..." -ForegroundColor Green

az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_ENV="production"

Write-Host "✅ FLASK_ENV set to production" -ForegroundColor Green
Write-Host "💰 No impact on Azure billing" -ForegroundColor Cyan
Write-Host "🛡️  Improved security posture" -ForegroundColor Green
