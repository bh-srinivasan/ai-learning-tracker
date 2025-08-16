# Fast Azure Deployment Script
# This script creates a local build and deploys via zip to avoid server-side builds

Write-Host "🚀 Fast Azure Deployment Starting..." -ForegroundColor Green
Write-Host ""

# Step 1: Configure Azure App Service for fast deployment
Write-Host "Step 1: Configuring Azure App Service settings..." -ForegroundColor Yellow
az webapp config appsettings set --name ai-learning-tracker-bharath --resource-group ai-learning-rg --settings WEBSITE_RUN_FROM_PACKAGE=1 --output none
az webapp config appsettings set --name ai-learning-tracker-bharath --resource-group ai-learning-rg --settings SCM_DO_BUILD_DURING_DEPLOYMENT=false --output none
Write-Host "✅ App Service configured for fast deployment" -ForegroundColor Green
Write-Host ""

# Step 2: Create deployment package locally
Write-Host "Step 2: Creating deployment package..." -ForegroundColor Yellow

# Create temporary package directory
if (Test-Path "./temp-package") {
    Remove-Item -Recurse -Force "./temp-package"
}
New-Item -ItemType Directory -Name "temp-package" | Out-Null

# Copy application files (excluding development artifacts)
$excludePatterns = @("*.db", "*.zip", "__pycache__", "*.pyc", ".git", ".venv", "temp-package", "node_modules", "backups", "cleanup-report-*", "tools")

Write-Host "  Copying application files..." -ForegroundColor White
Get-ChildItem -Path . | Where-Object { 
    $item = $_
    -not ($excludePatterns | Where-Object { $item.Name -like $_ }) 
} | Copy-Item -Destination "./temp-package" -Recurse -Force

Write-Host "  Package size: $([math]::Round((Get-ChildItem -Recurse ./temp-package | Measure-Object Length -Sum).Sum / 1MB, 2)) MB" -ForegroundColor Cyan

# Step 3: Create zip package
Write-Host "Step 3: Creating zip archive..." -ForegroundColor Yellow
if (Test-Path "./deploy-package.zip") {
    Remove-Item "./deploy-package.zip" -Force
}
Compress-Archive -Path "./temp-package/*" -DestinationPath "./deploy-package.zip" -Force
$zipSize = [math]::Round((Get-Item "./deploy-package.zip").Length / 1MB, 2)
Write-Host "✅ Zip package created: ${zipSize} MB" -ForegroundColor Green
Write-Host ""

# Step 4: Deploy to Azure
Write-Host "Step 4: Deploying to Azure App Service..." -ForegroundColor Yellow
$deployStart = Get-Date
az webapp deployment source config-zip --name ai-learning-tracker-bharath --resource-group ai-learning-rg --src "./deploy-package.zip"
$deployEnd = Get-Date
$deployTime = ($deployEnd - $deployStart).TotalSeconds

Write-Host "✅ Deployment completed in $([math]::Round($deployTime, 1)) seconds!" -ForegroundColor Green
Write-Host ""

# Step 5: Cleanup
Write-Host "Step 5: Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "./temp-package"
Remove-Item "./deploy-package.zip" -Force
Write-Host "✅ Cleanup completed" -ForegroundColor Green
Write-Host ""

# Step 6: Verification
Write-Host "🎯 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "App URL: https://ai-learning-tracker-bharath.azurewebsites.net" -ForegroundColor Magenta
Write-Host "Deployment time: $([math]::Round($deployTime, 1)) seconds (vs 5+ minutes with git push)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next time, just run: powershell ./fast-deploy.ps1" -ForegroundColor Yellow
