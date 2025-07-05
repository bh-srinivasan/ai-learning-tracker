#!/bin/bash
# Azure Environment Variables Setup Script
# Run this script in Azure CLI or Cloud Shell

echo "🌐 Setting up environment variables for AI Learning Tracker in Azure..."

APP_NAME="ai-learning-tracker-bharath"
RESOURCE_GROUP="AI_Learning_Tracker"

echo "📋 Setting environment variables..."

az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings ADMIN_PASSWORD="SecureAdminPass2024!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_USERNAME="demo"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DEMO_PASSWORD="DemoPass2024!"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_SECRET_KEY="supersecretkey-change-in-production-2024"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_ENV="production"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings FLASK_DEBUG="False"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DATABASE_URL="sqlite:///ai_learning.db"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings SESSION_TIMEOUT="3600"

echo "✅ Environment variables set successfully!"
echo "🔄 Restarting Azure App Service..."

az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

echo "🚀 Setup complete! Testing the deployment..."
echo "Production URL: https://$APP_NAME.azurewebsites.net"
echo ""
echo "New credentials:"
echo "Admin: admin / SecureAdminPass2024!"
echo "Demo:  demo / DemoPass2024!"
