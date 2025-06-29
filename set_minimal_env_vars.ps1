# Minimal Azure Environment Variables Setup
# Just the essentials for security and functionality

Write-Host "🌐 Setting MINIMAL environment variables for Azure..." -ForegroundColor Green

$APP_NAME = "ai-learning-tracker-bharath"
$RESOURCE_GROUP = "AI_Learning_Tracker"

# Essential credentials (MUST HAVE)
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings ADMIN_PASSWORD="YourSecureAdminPassword123!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_USERNAME="demo"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_PASSWORD="DemoUserPassword123!"

# Essential security (HIGHLY RECOMMENDED)
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_ENV="production"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_DEBUG="False"

Write-Host "✅ Minimal setup complete!" -ForegroundColor Green
Write-Host "⚠️  Note: SECRET_KEY will auto-generate (sessions reset on app restart)" -ForegroundColor Yellow
Write-Host "⚠️  Note: SESSION_TIMEOUT defaults to 1 hour" -ForegroundColor Yellow

# Restart the app
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

Write-Host "🚀 App restarted with minimal configuration!" -ForegroundColor Green
