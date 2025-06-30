# Azure Environment Variables Setup - Using Your .env Values
# Run these commands in Azure CLI or Cloud Shell

# Set your app details
$APP_NAME = "ai-learning-tracker-bharath"
$RESOURCE_GROUP = "AI_Learning_Tracker"

Write-Host "🌐 Setting environment variables in Azure App Service..." -ForegroundColor Green

# Set each environment variable using your .env values
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings ADMIN_PASSWORD="YourSecureAdminPassword123!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_USERNAME="demo"  
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_PASSWORD="DemoUserPassword123!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_SECRET_KEY="your-super-secret-key-change-this-in-production"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_ENV="production"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_DEBUG="False"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DATABASE_URL="sqlite:///ai_learning.db"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings SESSION_TIMEOUT="3600"

Write-Host "✅ All environment variables set!" -ForegroundColor Green
Write-Host "🔄 Restarting app service..." -ForegroundColor Yellow

# Restart the app service
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

Write-Host "🚀 Setup complete!" -ForegroundColor Green
Write-Host "Your new credentials are:" -ForegroundColor Cyan
Write-Host "Admin: admin / YourSecureAdminPassword123!" -ForegroundColor White
Write-Host "Demo:  demo / DemoUserPassword123!" -ForegroundColor White
Write-Host "Production URL: https://ai-learning-tracker-bharath.azurewebsites.net" -ForegroundColor Yellow
