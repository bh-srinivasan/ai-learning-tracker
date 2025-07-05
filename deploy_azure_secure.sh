#!/bin/bash

# 🚀 Azure Deployment Script for AI Learning Tracker
# This script deploys the secured application to Azure App Service

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-ai-learning-rg}"
APP_NAME="${AZURE_APP_NAME:-ai-learning-tracker}"
LOCATION="${AZURE_LOCATION:-East US}"
PLAN_NAME="${AZURE_PLAN_NAME:-ai-learning-plan}"
PLAN_SKU="${AZURE_PLAN_SKU:-B1}"

echo "🚀 Starting Azure deployment for AI Learning Tracker"
echo "====================================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "Location: $LOCATION"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Azure CLI is ready"

# Create resource group if it doesn't exist
echo "📦 Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

# Create App Service plan if it doesn't exist
echo "📋 Creating App Service plan..."
az appservice plan create \
    --name "$PLAN_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --sku "$PLAN_SKU" \
    --is-linux \
    --output table

# Create App Service
echo "🌐 Creating App Service..."
az webapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$PLAN_NAME" \
    --runtime "PYTHON|3.10" \
    --output table

# Configure environment variables
echo "⚙️  Configuring environment variables..."

# Prompt for secure passwords if not set
if [[ -z "$ADMIN_PASSWORD" ]]; then
    read -s -p "Enter secure admin password: " ADMIN_PASSWORD
    echo ""
fi

if [[ -z "$DEMO_PASSWORD" ]]; then
    read -s -p "Enter secure demo password: " DEMO_PASSWORD
    echo ""
fi

if [[ -z "$FLASK_SECRET_KEY" ]]; then
    FLASK_SECRET_KEY=$(openssl rand -base64 32)
    echo "Generated secure Flask secret key"
fi

# Set all environment variables
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings \
        FLASK_ENV=production \
        NODE_ENV=production \
        ADMIN_PASSWORD="$ADMIN_PASSWORD" \
        DEMO_PASSWORD="$DEMO_PASSWORD" \
        FLASK_SECRET_KEY="$FLASK_SECRET_KEY" \
        DATABASE_URL="sqlite:///ai_learning.db" \
        SESSION_TIMEOUT=3600 \
        PASSWORD_MIN_LENGTH=8 \
    --output table

echo "✅ Environment variables configured"

# Enable logging
echo "📝 Enabling application logging..."
az webapp log config \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --application-logging filesystem \
    --level information \
    --output table

# Configure startup command
echo "🚀 Configuring startup command..."
az webapp config set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --startup-file "startup.py" \
    --output table

# Create deployment package
echo "📦 Creating deployment package..."
DEPLOYMENT_DIR="deployment_temp"
mkdir -p "$DEPLOYMENT_DIR"

# Copy application files (excluding development files)
cp -r \
    app.py \
    startup.py \
    requirements.txt \
    security_guard.py \
    production_config.py \
    auth/ \
    admin/ \
    dashboard/ \
    learnings/ \
    courses/ \
    recommendations/ \
    templates/ \
    static/ \
    "$DEPLOYMENT_DIR/"

# Create web.config for Azure
cat > "$DEPLOYMENT_DIR/web.config" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="python" arguments="startup.py" stdoutLogEnabled="true" stdoutLogFile="python.log" startupTimeLimit="60" requestTimeout="00:04:00">
      <environmentVariables>
        <environmentVariable name="PORT" value="%HTTP_PLATFORM_PORT%" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
EOF

# Create deployment zip
cd "$DEPLOYMENT_DIR"
zip -r ../deployment.zip . -x "*.pyc" "*/__pycache__/*" "*.env*" "test_*" "*_test.py"
cd ..

echo "✅ Deployment package created"

# Deploy to Azure
echo "🚀 Deploying to Azure App Service..."
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --src deployment.zip

echo "✅ Deployment completed"

# Clean up
rm -rf "$DEPLOYMENT_DIR" deployment.zip

# Get app URL
APP_URL=$(az webapp show --resource-group "$RESOURCE_GROUP" --name "$APP_NAME" --query "defaultHostName" --output tsv)

echo ""
echo "🎉 Deployment Successful!"
echo "========================"
echo "App URL: https://$APP_URL"
echo "Admin Username: admin"
echo "Demo Username: demo"
echo ""
echo "Next Steps:"
echo "1. Visit the app URL to verify it's working"
echo "2. Test admin login with the password you provided"
echo "3. Test user management functionality"
echo "4. Monitor logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo ""
echo "🔒 Security Features Enabled:"
echo "- Multi-layer user management protection"
echo "- Environment-based configuration"
echo "- Production safety guards"
echo "- Audit logging"
echo "- UI-only sensitive operations"
echo ""
echo "📋 To view logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
