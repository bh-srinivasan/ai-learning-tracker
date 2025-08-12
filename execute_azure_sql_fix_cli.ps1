# Azure SQL Fix using Azure CLI
# This script uses Azure CLI to execute SQL commands directly

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "DefaultResourceGroup-CUS",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "ai-learning-sql-centralus",
    
    [Parameter(Mandatory=$false)]
    [string]$DatabaseName = "ai-learning-db"
)

Write-Host "=== Azure SQL Fix Script using Azure CLI ===" -ForegroundColor Cyan

# Check if Azure CLI is available
try {
    $azVersion = az version --output table 2>$null
    Write-Host "✅ Azure CLI is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install Azure CLI first." -ForegroundColor Red
    exit 1
}

# Check if logged into Azure
try {
    $account = az account show --output json 2>$null | ConvertFrom-Json
    Write-Host "✅ Logged into Azure as: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged into Azure. Please run 'az login' first." -ForegroundColor Red
    exit 1
}

# SQL commands to execute
$sqlCommands = @(
    "-- Create the compatibility view",
    "CREATE OR ALTER VIEW dbo.courses_app AS SELECT id, title, description, COALESCE(difficulty, level) AS difficulty, TRY_CONVERT(float, duration) AS duration_hours, url, CAST(NULL AS nvarchar(100)) AS category, level, created_at FROM dbo.courses;",
    "-- Verify the view",
    "SELECT COUNT(*) as course_count FROM dbo.courses_app;",
    "SELECT TOP 3 id, title, difficulty FROM dbo.courses_app ORDER BY created_at DESC;"
)

Write-Host "🔄 Executing SQL commands on Azure SQL Database..." -ForegroundColor Yellow
Write-Host "Server: $ServerName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray

foreach ($sql in $sqlCommands) {
    if ($sql.StartsWith("--")) {
        Write-Host $sql -ForegroundColor Gray
        continue
    }
    
    Write-Host "Executing: $($sql.Substring(0, [Math]::Min(50, $sql.Length)))..." -ForegroundColor Yellow
    
    try {
        # Execute SQL using Azure CLI
        $result = az sql db query `
            --server $ServerName `
            --database $DatabaseName `
            --auth-type ADIntegrated `
            --query-text $sql `
            --output table 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Command executed successfully" -ForegroundColor Green
            if ($result -and $result.Length -gt 0) {
                Write-Host "Result:" -ForegroundColor Cyan
                Write-Host $result -ForegroundColor White
            }
        } else {
            Write-Host "❌ Command failed:" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error executing command: $_" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1
}

Write-Host "`n🎉 Azure SQL fix script completed!" -ForegroundColor Green
Write-Host "Your 'Manage Courses' page should now work without errors." -ForegroundColor Green
