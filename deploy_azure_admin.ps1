# Azure Admin User Deployment Script
# Run this locally to execute the admin user creation on Azure

param(
    [string]$WebAppName = "ai-learning-tracker-bharath",
    [string]$ResourceGroup = "rg-ai-learning-tracker",
    [switch]$DryRun = $false
)

Write-Host "=== AZURE ADMIN USER DEPLOYMENT ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# Check if Azure CLI is installed
try {
    $azVersion = az version --output tsv 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI not found"
    }
    Write-Host "✅ Azure CLI detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI is required but not installed" -ForegroundColor Red
    Write-Host "   Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check login status
try {
    $account = az account show --output json 2>$null | ConvertFrom-Json
    if ($account) {
        Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
        Write-Host "   Subscription: $($account.name)" -ForegroundColor Gray
    } else {
        throw "Not logged in"
    }
} catch {
    Write-Host "❌ Not logged in to Azure" -ForegroundColor Red
    Write-Host "   Run: az login" -ForegroundColor Yellow
    exit 1
}

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Upload and execute the initialization script
Write-Host "🚀 Deploying admin user initialization script..." -ForegroundColor Cyan

try {
    # Create a temp directory for the script
    $tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
    $scriptPath = Join-Path $tempDir "initialize_azure_admin.py"
    
    # Copy our script to temp directory
    Copy-Item "initialize_azure_admin.py" $scriptPath
    
    if (-not $DryRun) {
        # Execute the script via Azure CLI
        Write-Host "📤 Uploading and executing initialization script..." -ForegroundColor Blue
        
        $command = "cd /home/site/wwwroot; python initialize_azure_admin.py"
        $result = az webapp ssh --resource-group $ResourceGroup --name $WebAppName --command $command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Script executed successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Script Output:" -ForegroundColor Cyan
            Write-Host $result -ForegroundColor White
        } else {
            Write-Host "❌ Script execution failed" -ForegroundColor Red
            Write-Host "Error: $result" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "🔍 Would execute: az webapp ssh --resource-group $ResourceGroup --name $WebAppName --command '$command'" -ForegroundColor Yellow
    }
    
    # Cleanup
    Remove-Item $tempDir -Recurse -Force
    
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Your application should now be ready:" -ForegroundColor Cyan
Write-Host "   URL: https://$WebAppName.azurewebsites.net/" -ForegroundColor Blue
Write-Host "   Username: admin" -ForegroundColor Blue
Write-Host "   Password: [from environment variable]" -ForegroundColor Blue
Write-Host ""
Write-Host "🧪 Test the login to verify everything works!" -ForegroundColor Yellow
