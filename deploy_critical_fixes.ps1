# Azure Deployment Script for Critical Fixes (PowerShell)
# Deploy the restored modules and upload fixes to Azure App Service

Write-Host "🚀 Azure Deployment - Critical Fixes" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Configuration
$ResourceGroup = "ai-learning-rg"
$AppName = "ai-learning-tracker"
$Location = "East US"

Write-Host "📋 Deployment Configuration:" -ForegroundColor Cyan
Write-Host "   Resource Group: $ResourceGroup"
Write-Host "   App Name: $AppName" 
Write-Host "   Location: $Location"
Write-Host ""

# Check if Azure CLI is installed
try {
    az version | Out-Null
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install Azure CLI first." -ForegroundColor Red
    Write-Host "   Download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Login check
Write-Host "🔐 Checking Azure login status..." -ForegroundColor Cyan
try {
    az account show | Out-Null
    Write-Host "✅ Azure login verified" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged into Azure. Please login first:" -ForegroundColor Red
    Write-Host "   az login"
    exit 1
}

# Get current account info
Write-Host "📊 Current Azure Account:" -ForegroundColor Cyan
az account show --output table

# Check if resource group exists
Write-Host "🔍 Checking if resource group exists..." -ForegroundColor Cyan
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq "false") {
    Write-Host "⚠️  Resource group '$ResourceGroup' not found" -ForegroundColor Yellow
    Write-Host "📝 Creating resource group..." -ForegroundColor Cyan
    
    az group create --name $ResourceGroup --location $Location
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Resource group created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create resource group" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Resource group exists" -ForegroundColor Green
}

# Check if app service exists
Write-Host "🔍 Checking if App Service exists..." -ForegroundColor Cyan
try {
    az webapp show --resource-group $ResourceGroup --name $AppName | Out-Null
    Write-Host "✅ App Service exists" -ForegroundColor Green
} catch {
    Write-Host "⚠️  App Service '$AppName' not found" -ForegroundColor Yellow
    Write-Host "📝 Creating App Service..." -ForegroundColor Cyan
    
    # Create App Service Plan first
    Write-Host "📝 Creating App Service Plan..." -ForegroundColor Cyan
    az appservice plan create `
        --name "$AppName-plan" `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku F1 `
        --is-linux
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create App Service Plan" -ForegroundColor Red
        exit 1
    }
    
    # Create App Service
    Write-Host "📝 Creating App Service..." -ForegroundColor Cyan
    az webapp create `
        --resource-group $ResourceGroup `
        --plan "$AppName-plan" `
        --name $AppName `
        --runtime "PYTHON|3.11" `
        --deployment-local-git
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ App Service created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create App Service" -ForegroundColor Red
        exit 1
    }
}

# Configure deployment settings
Write-Host "⚙️  Configuring deployment settings..." -ForegroundColor Cyan

# Set Python version and startup command
az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --linux-fx-version "PYTHON|3.11" `
    --startup-file "wsgi.py"

# Configure app settings
Write-Host "⚙️  Setting application configuration..." -ForegroundColor Cyan
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings `
    FLASK_ENV=production `
    FLASK_APP=app.py `
    SCM_DO_BUILD_DURING_DEPLOYMENT=true `
    ENABLE_ORYX_BUILD=true

# Deploy from local git (current directory)
Write-Host "📦 Deploying application..." -ForegroundColor Cyan
Write-Host "⚠️  Note: Make sure you have committed all changes to git before deploying" -ForegroundColor Yellow

# Get deployment credentials
Write-Host "🔑 Getting deployment credentials..." -ForegroundColor Cyan
$DeployUrl = az webapp deployment source config-local-git `
    --resource-group $ResourceGroup `
    --name $AppName `
    --output tsv

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment URL obtained" -ForegroundColor Green
    Write-Host "📡 Deployment URL: $DeployUrl" -ForegroundColor Cyan
    
    # Add Azure remote if it doesn't exist
    try {
        git remote get-url azure | Out-Null
        Write-Host "📝 Updating Azure remote..." -ForegroundColor Cyan
        git remote set-url azure $DeployUrl
    } catch {
        Write-Host "📝 Adding Azure remote..." -ForegroundColor Cyan
        git remote add azure $DeployUrl
    }
    
    Write-Host "🚀 Pushing to Azure..." -ForegroundColor Green
    Write-Host "⚠️  You may be prompted for deployment credentials" -ForegroundColor Yellow
    git push azure master
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
        Write-Host "✅ Critical fixes have been deployed to Azure" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
        Write-Host "   ✅ Restored modules: fast_course_fetcher.py, course_validator.py, deployment_safety.py, azure_database_sync.py"
        Write-Host "   ✅ Fixed file upload errors"
        Write-Host "   ✅ Enhanced error handling"  
        Write-Host "   ✅ Production safety checks enabled"
        Write-Host ""
        Write-Host "🌐 Your app is available at:" -ForegroundColor Cyan
        Write-Host "   https://$AppName.azurewebsites.net"
        Write-Host ""
        Write-Host "🔍 Monitor deployment:" -ForegroundColor Cyan
        Write-Host "   az webapp log tail --resource-group $ResourceGroup --name $AppName"
        
    } else {
        Write-Host "❌ Deployment failed" -ForegroundColor Red
        Write-Host "💡 Troubleshooting tips:" -ForegroundColor Yellow
        Write-Host "   1. Check your deployment credentials"
        Write-Host "   2. Ensure all changes are committed to git"
        Write-Host "   3. Check Azure portal for detailed logs"
        exit 1
    }
    
} else {
    Write-Host "❌ Failed to get deployment URL" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎯 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Test the deployed application"
Write-Host "2. Verify file upload functionality works"
Write-Host "3. Check admin panel features"
Write-Host "4. Monitor application logs for any issues"
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Cyan
Write-Host "   Monitor logs: az webapp log tail --resource-group $ResourceGroup --name $AppName"
Write-Host "   Restart app:  az webapp restart --resource-group $ResourceGroup --name $AppName"
Write-Host "   App settings: az webapp config appsettings list --resource-group $ResourceGroup --name $AppName"
