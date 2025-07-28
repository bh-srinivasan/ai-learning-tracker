#!/bin/bash
# Azure App Service Configuration Script
# Run this to configure Azure environment variables

echo "Configuring Azure App Service..."

# Set startup command
az webapp config set --name ai-learning-tracker-bharath --resource-group your-resource-group --startup-file "python main.py"

# Set application settings
az webapp config appsettings set --name ai-learning-tracker-bharath --resource-group your-resource-group --settings \
    FLASK_ENV=production \
    FLASK_DEBUG=False \
    PYTHONPATH=. \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    ENABLE_ORYX_BUILD=true

echo "Azure configuration complete!"
echo "Note: Update the resource group name in this script"
