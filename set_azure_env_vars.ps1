# Azure Environment Variables Setup Script (PowerShell)
# Run this script in Azure CLI or Cloud Shell

Write-Host "🌐 Setting up environment variables for AI Learning Tracker in Azure..." -ForegroundColor Green

$APP_NAME = "ai-learning-tracker-bharath"
$RESOURCE_GROUP = "AI_Learning_Tracker"

Write-Host "📋 Setting environment variables..." -ForegroundColor Yellow

az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings ADMIN_PASSWORD="SecureAdminPass2024!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_USERNAME="demo"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_PASSWORD="DemoPass2024!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_SECRET_KEY="supersecretkey-change-in-production-2024"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_ENV="production"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_DEBUG="False"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DATABASE_URL="sqlite:///ai_learning.db"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings SESSION_TIMEOUT="3600"

Write-Host "✅ Environment variables set successfully!" -ForegroundColor Green
Write-Host "🔄 Restarting Azure App Service..." -ForegroundColor Yellow

az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

Write-Host "🚀 Setup complete! Testing the deployment..." -ForegroundColor Green
Write-Host "Production URL: https://$APP_NAME.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Write-Host "New credentials:" -ForegroundColor Yellow
Write-Host "Admin: admin / SecureAdminPass2024!" -ForegroundColor White
Write-Host "Demo:  demo / DemoPass2024!" -ForegroundColor White
