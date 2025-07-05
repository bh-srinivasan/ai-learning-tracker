# 🚀 Azure Deployment Script for AI Learning Tracker (PowerShell)
# This script deploys the secured application to Azure App Service

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "ai-learning-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$AppName = "ai-learning-tracker",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$false)]
    [string]$PlanName = "ai-learning-plan",
    
    [Parameter(Mandatory=$false)]
    [string]$PlanSku = "B1"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Azure deployment for AI Learning Tracker" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "App Name: $AppName" -ForegroundColor Yellow
Write-Host "Location: $Location" -ForegroundColor Yellow
Write-Host ""

# Check if Azure CLI is installed
try {
    az --version | Out-Null
    Write-Host "✅ Azure CLI is ready" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if logged in to Azure
try {
    az account show | Out-Null
    Write-Host "✅ Azure authentication verified" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Azure. Please run 'az login' first." -ForegroundColor Red
    exit 1
}

# Create resource group if it doesn't exist
Write-Host "📦 Creating resource group..." -ForegroundColor Blue
az group create --name $ResourceGroup --location $Location --output table

# Create App Service plan if it doesn't exist
Write-Host "📋 Creating App Service plan..." -ForegroundColor Blue
az appservice plan create `
    --name $PlanName `
    --resource-group $ResourceGroup `
    --sku $PlanSku `
    --is-linux `
    --output table

# Create App Service
Write-Host "🌐 Creating App Service..." -ForegroundColor Blue
az webapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --plan $PlanName `
    --runtime "PYTHON|3.10" `
    --output table

# Configure environment variables
Write-Host "⚙️  Configuring environment variables..." -ForegroundColor Blue

# Prompt for secure passwords
$AdminPassword = Read-Host -Prompt "Enter secure admin password" -AsSecureString
$AdminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword))

$DemoPassword = Read-Host -Prompt "Enter secure demo password" -AsSecureString
$DemoPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($DemoPassword))

# Generate secure Flask secret key
$FlaskSecretKey = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes([System.Guid]::NewGuid().ToString() + [System.DateTime]::Now.Ticks))
Write-Host "Generated secure Flask secret key" -ForegroundColor Green

# Set all environment variables
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings `
        FLASK_ENV=production `
        NODE_ENV=production `
        ADMIN_PASSWORD=$AdminPasswordPlain `
        DEMO_PASSWORD=$DemoPasswordPlain `
        FLASK_SECRET_KEY=$FlaskSecretKey `
        DATABASE_URL="sqlite:///ai_learning.db" `
        SESSION_TIMEOUT=3600 `
        PASSWORD_MIN_LENGTH=8 `
    --output table

Write-Host "✅ Environment variables configured" -ForegroundColor Green

# Enable logging
Write-Host "📝 Enabling application logging..." -ForegroundColor Blue
az webapp log config `
    --resource-group $ResourceGroup `
    --name $AppName `
    --application-logging filesystem `
    --level information `
    --output table

# Configure startup command
Write-Host "🚀 Configuring startup command..." -ForegroundColor Blue
az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --startup-file "startup.py" `
    --output table

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Blue
$DeploymentDir = "deployment_temp"
if (Test-Path $DeploymentDir) {
    Remove-Item -Recurse -Force $DeploymentDir
}
New-Item -ItemType Directory -Path $DeploymentDir

# Copy application files (excluding development files)
$FilesToCopy = @(
    "app.py",
    "startup.py", 
    "requirements.txt",
    "security_guard.py",
    "production_config.py",
    "auth",
    "admin", 
    "dashboard",
    "learnings",
    "courses",
    "recommendations",
    "templates",
    "static"
)

foreach ($file in $FilesToCopy) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $DeploymentDir -Recurse -Force
        Write-Host "Copied: $file" -ForegroundColor Gray
    }
}

# Create web.config for Azure
$WebConfig = @'
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
'@

Set-Content -Path "$DeploymentDir\web.config" -Value $WebConfig

# Create deployment zip
Write-Host "📦 Creating deployment archive..." -ForegroundColor Blue
Compress-Archive -Path "$DeploymentDir\*" -DestinationPath "deployment.zip" -Force

Write-Host "✅ Deployment package created" -ForegroundColor Green

# Deploy to Azure
Write-Host "🚀 Deploying to Azure App Service..." -ForegroundColor Blue
az webapp deployment source config-zip `
    --resource-group $ResourceGroup `
    --name $AppName `
    --src deployment.zip

Write-Host "✅ Deployment completed" -ForegroundColor Green

# Clean up
Remove-Item -Recurse -Force $DeploymentDir
Remove-Item -Force deployment.zip

# Get app URL
$AppUrl = az webapp show --resource-group $ResourceGroup --name $AppName --query "defaultHostName" --output tsv

Write-Host ""
Write-Host "🎉 Deployment Successful!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host "App URL: https://$AppUrl" -ForegroundColor Yellow
Write-Host "Admin Username: admin" -ForegroundColor Yellow
Write-Host "Demo Username: demo" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Visit the app URL to verify it's working" -ForegroundColor White
Write-Host "2. Test admin login with the password you provided" -ForegroundColor White
Write-Host "3. Test user management functionality" -ForegroundColor White
Write-Host "4. Monitor logs: az webapp log tail --resource-group $ResourceGroup --name $AppName" -ForegroundColor White
Write-Host ""
Write-Host "🔒 Security Features Enabled:" -ForegroundColor Green
Write-Host "- Multi-layer user management protection" -ForegroundColor White
Write-Host "- Environment-based configuration" -ForegroundColor White
Write-Host "- Production safety guards" -ForegroundColor White
Write-Host "- Audit logging" -ForegroundColor White
Write-Host "- UI-only sensitive operations" -ForegroundColor White
Write-Host ""
Write-Host "📋 To view logs: az webapp log tail --resource-group $ResourceGroup --name $AppName" -ForegroundColor Cyan

# Clear sensitive variables
$AdminPasswordPlain = $null
$DemoPasswordPlain = $null
$FlaskSecretKey = $null
