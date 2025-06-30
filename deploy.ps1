# deploy.ps1 - Automated deployment script for AI Learning Tracker

Write-Host "Starting AI Learning Tracker deployment..." -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path -Path ".git")) {
    Write-Host "Error: Not in a git repository!" -ForegroundColor Red
    exit 1
}

# Check for uncommitted changes
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "Staging all changes..." -ForegroundColor Yellow
    git add .
    
    # Get commit message from user or use default
    $commitMessage = Read-Host "Enter commit message (or press Enter for auto-generated)"
    if (-not $commitMessage) {
        $commitMessage = "Update AI Learning Tracker - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }
    
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git commit -m $commitMessage
}
else {
    Write-Host "No changes to commit" -ForegroundColor Green
}

# Push to GitHub if origin remote exists
$hasOrigin = git remote get-url origin 2>$null
if ($hasOrigin) {
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    try {
        git push origin master
        Write-Host "Successfully pushed to GitHub" -ForegroundColor Green
    }
    catch {
        Write-Host "Warning: Could not push to GitHub - $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "GitHub remote not configured. Skipping GitHub push." -ForegroundColor Yellow
    Write-Host "To set up GitHub, run: git remote add origin https://github.com/USERNAME/REPO.git" -ForegroundColor Cyan
}

# Push to Azure for deployment
Write-Host "Deploying to Azure App Service..." -ForegroundColor Yellow
try {
    git push azure master
    Write-Host "Successfully deployed to Azure!" -ForegroundColor Green
    Write-Host "Your app is live at: https://ai-learning-tracker-bharath.azurewebsites.net/" -ForegroundColor Cyan
}
catch {
    Write-Host "Azure deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor White
Write-Host "   Code committed to git" -ForegroundColor Green
if ($hasOrigin) {
    Write-Host "   Pushed to GitHub repository" -ForegroundColor Green
}
Write-Host "   Deployed to Azure App Service" -ForegroundColor Green
Write-Host "   Live URL: https://ai-learning-tracker-bharath.azurewebsites.net/" -ForegroundColor Cyan

# Optional: Open the deployed app in browser
$openBrowser = Read-Host "Open the deployed app in browser? (y/N)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "https://ai-learning-tracker-bharath.azurewebsites.net/"
}
