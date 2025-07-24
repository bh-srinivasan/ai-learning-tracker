#!/bin/bash
# Azure Deployment Script for Critical Fixes
# Deploy the restored modules and upload fixes to Azure App Service

echo "🚀 Azure Deployment - Critical Fixes"
echo "====================================="

# Configuration
RESOURCE_GROUP="ai-learning-rg"
APP_NAME="ai-learning-tracker"
LOCATION="East US"

echo "📋 Deployment Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Name: $APP_NAME"
echo "   Location: $LOCATION"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install Azure CLI first."
    echo "   Download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo "✅ Azure CLI found"

# Login check
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please login first:"
    echo "   az login"
    exit 1
fi

echo "✅ Azure login verified"

# Get current account info
ACCOUNT_INFO=$(az account show --output table)
echo "📊 Current Azure Account:"
echo "$ACCOUNT_INFO"
echo ""

# Check if resource group exists
echo "🔍 Checking if resource group exists..."
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "⚠️  Resource group '$RESOURCE_GROUP' not found"
    echo "📝 Creating resource group..."
    az group create --name $RESOURCE_GROUP --location "$LOCATION"
    if [ $? -eq 0 ]; then
        echo "✅ Resource group created successfully"
    else
        echo "❌ Failed to create resource group"
        exit 1
    fi
else
    echo "✅ Resource group exists"
fi

# Check if app service exists
echo "🔍 Checking if App Service exists..."
if ! az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME &> /dev/null; then
    echo "⚠️  App Service '$APP_NAME' not found"
    echo "📝 Creating App Service..."
    
    # Create App Service Plan first
    echo "📝 Creating App Service Plan..."
    az appservice plan create \
        --name "${APP_NAME}-plan" \
        --resource-group $RESOURCE_GROUP \
        --location "$LOCATION" \
        --sku F1 \
        --is-linux
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create App Service Plan"
        exit 1
    fi
    
    # Create App Service
    echo "📝 Creating App Service..."
    az webapp create \
        --resource-group $RESOURCE_GROUP \
        --plan "${APP_NAME}-plan" \
        --name $APP_NAME \
        --runtime "PYTHON|3.11" \
        --deployment-local-git
    
    if [ $? -eq 0 ]; then
        echo "✅ App Service created successfully"
    else
        echo "❌ Failed to create App Service"
        exit 1
    fi
else
    echo "✅ App Service exists"
fi

# Configure deployment settings
echo "⚙️  Configuring deployment settings..."

# Set Python version and startup command
az webapp config set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --linux-fx-version "PYTHON|3.11" \
    --startup-file "wsgi.py"

# Configure app settings
echo "⚙️  Setting application configuration..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    FLASK_ENV=production \
    FLASK_APP=app.py \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    ENABLE_ORYX_BUILD=true

# Deploy from local git (current directory)
echo "📦 Deploying application..."
echo "⚠️  Note: Make sure you have committed all changes to git before deploying"

# Get deployment credentials
echo "🔑 Getting deployment credentials..."
DEPLOY_URL=$(az webapp deployment source config-local-git \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --output tsv)

if [ $? -eq 0 ]; then
    echo "✅ Deployment URL obtained"
    echo "📡 Deployment URL: $DEPLOY_URL"
    
    # Add Azure remote if it doesn't exist
    if ! git remote get-url azure &> /dev/null; then
        echo "📝 Adding Azure remote..."
        git remote add azure $DEPLOY_URL
    else
        echo "📝 Updating Azure remote..."
        git remote set-url azure $DEPLOY_URL
    fi
    
    echo "🚀 Pushing to Azure..."
    echo "⚠️  You may be prompted for deployment credentials"
    git push azure master
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 DEPLOYMENT SUCCESSFUL!"
        echo "✅ Critical fixes have been deployed to Azure"
        echo ""
        echo "📊 Deployment Summary:"
        echo "   ✅ Restored modules: fast_course_fetcher.py, course_validator.py, deployment_safety.py, azure_database_sync.py"
        echo "   ✅ Fixed file upload errors"
        echo "   ✅ Enhanced error handling"
        echo "   ✅ Production safety checks enabled"
        echo ""
        echo "🌐 Your app is available at:"
        echo "   https://$APP_NAME.azurewebsites.net"
        echo ""
        echo "🔍 Monitor deployment:"
        echo "   az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
        
    else
        echo "❌ Deployment failed"
        echo "💡 Troubleshooting tips:"
        echo "   1. Check your deployment credentials"
        echo "   2. Ensure all changes are committed to git"
        echo "   3. Check Azure portal for detailed logs"
        exit 1
    fi
    
else
    echo "❌ Failed to get deployment URL"
    exit 1
fi

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Test the deployed application"
echo "2. Verify file upload functionality works"
echo "3. Check admin panel features"
echo "4. Monitor application logs for any issues"
echo ""
echo "📋 Useful commands:"
echo "   Monitor logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "   Restart app:  az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "   App settings: az webapp config appsettings list --resource-group $RESOURCE_GROUP --name $APP_NAME"
