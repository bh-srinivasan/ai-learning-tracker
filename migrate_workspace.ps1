# Workspace Migration Script
# This script will help move the AI_Learning workspace from OneDrive to Downloads

$sourceDir = "c:\Users\bhsrinivasan\OneDrive - Microsoft\Bharath\Common\Learning\Copilot Tests\AI_Learning"
$targetBaseDir = "c:\Users\bhsrinivasan\Downloads"

# Function to move workspace
function Move-Workspace {
    param(
        [string]$targetFolderName
    )
    
    $targetDir = Join-Path $targetBaseDir $targetFolderName
    
    Write-Host "🔄 Moving AI_Learning workspace..." -ForegroundColor Yellow
    Write-Host "   From: $sourceDir" -ForegroundColor Gray
    Write-Host "   To:   $targetDir" -ForegroundColor Gray
    
    # Check if source exists
    if (-not (Test-Path $sourceDir)) {
        Write-Host "❌ Source directory not found: $sourceDir" -ForegroundColor Red
        return $false
    }
    
    # Check if target already exists
    if (Test-Path $targetDir) {
        Write-Host "⚠️  Target directory already exists: $targetDir" -ForegroundColor Yellow
        $response = Read-Host "Do you want to overwrite? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Host "❌ Operation cancelled" -ForegroundColor Red
            return $false
        }
        Remove-Item $targetDir -Recurse -Force
    }
    
    try {
        # Create target directory
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        
        # Copy all files and folders
        Copy-Item -Path "$sourceDir\*" -Destination $targetDir -Recurse -Force
        
        Write-Host "✅ Workspace copied successfully!" -ForegroundColor Green
        
        # Verify critical files
        $criticalFiles = @(
            "app.py",
            "ai_learning.db", 
            "requirements.txt",
            ".git"
        )
        
        Write-Host "🔍 Verifying critical files..." -ForegroundColor Yellow
        foreach ($file in $criticalFiles) {
            $filePath = Join-Path $targetDir $file
            if (Test-Path $filePath) {
                Write-Host "   ✅ $file" -ForegroundColor Green
            } else {
                Write-Host "   ❌ $file (missing)" -ForegroundColor Red
            }
        }
        
        # Check git status
        Set-Location $targetDir
        $gitStatus = git status 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Git repository" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Git repository (may need re-initialization)" -ForegroundColor Yellow
        }
        
        Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
        Write-Host "   1. Open the new workspace in VS Code: $targetDir" -ForegroundColor Gray
        Write-Host "   2. Recreate virtual environment if needed" -ForegroundColor Gray
        Write-Host "   3. Test the application: python app.py" -ForegroundColor Gray
        Write-Host "   4. Verify git status: git status" -ForegroundColor Gray
        Write-Host "   5. Remove old directory if everything works: $sourceDir" -ForegroundColor Gray
        
        return $true
        
    } catch {
        Write-Host "❌ Error during migration: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Example usage:
# Move-Workspace "AI_Learning_Secure"

Write-Host "🚀 Workspace Migration Script Ready!" -ForegroundColor Green
Write-Host "Usage: Move-Workspace 'YourTargetFolderName'" -ForegroundColor Yellow
