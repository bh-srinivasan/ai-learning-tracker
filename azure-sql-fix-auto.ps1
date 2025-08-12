# Azure SQL Fix Automation Script
# This script connects to Azure SQL and creates the missing courses_app view

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "ai-learning-sql-centralus.database.windows.net",
    
    [Parameter(Mandatory=$false)]
    [string]$DatabaseName = "ai-learning-db",
    
    [Parameter(Mandatory=$false)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [Security.SecureString]$Password
)

Write-Host "=== Azure SQL Fix: Creating courses_app View ===" -ForegroundColor Cyan
Write-Host ""

# Import SqlServer module if available
try {
    Import-Module SqlServer -ErrorAction Stop
    Write-Host "[OK] SqlServer PowerShell module loaded" -ForegroundColor Green
}
catch {
    Write-Host "[WARNING] SqlServer module not available. Please install it:" -ForegroundColor Yellow
    Write-Host "  Install-Module -Name SqlServer -Scope CurrentUser" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative: Execute the SQL manually in Azure Portal" -ForegroundColor Yellow
    Write-Host "See: AZURE_SQL_FIX_INSTRUCTIONS.md" -ForegroundColor White
    exit 1
}

# Get credentials if not provided
if (-not $Username) {
    $Username = $env:AZURE_SQL_USERNAME
    if (-not $Username) {
        $Username = Read-Host "Enter Azure SQL Username"
    }
}

if (-not $Password) {
    # Try to get from environment first
    $EnvPassword = $env:AZURE_SQL_PASSWORD
    if ($EnvPassword) {
        $Password = ConvertTo-SecureString $EnvPassword -AsPlainText -Force
    } else {
        $Password = Read-Host "Enter Azure SQL Password" -AsSecureString
    }
}

# Convert SecureString to plain text for SQL connection
$PlainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password))

# SQL Script to create the view
$SqlScript = @"
-- Create the compatibility view
CREATE OR ALTER VIEW dbo.courses_app AS
SELECT 
    id,
    title,
    description,
    COALESCE(difficulty, level) AS difficulty,
    TRY_CONVERT(float, duration) AS duration_hours,
    url,
    CAST(NULL AS nvarchar(100)) AS category,
    level,
    created_at
FROM dbo.courses;

-- Verify the view
SELECT COUNT(*) AS course_count FROM dbo.courses_app;
SELECT TOP 3 id, title, difficulty, duration_hours FROM dbo.courses_app;
"@

try {
    Write-Host "[INFO] Connecting to Azure SQL Database..." -ForegroundColor Blue
    Write-Host "  Server: $ServerName" -ForegroundColor White
    Write-Host "  Database: $DatabaseName" -ForegroundColor White
    Write-Host "  User: $Username" -ForegroundColor White
    Write-Host ""
    
    # Execute the SQL script
    $Results = Invoke-Sqlcmd -ServerInstance $ServerName -Database $DatabaseName -Username $Username -Password $PlainPassword -Query $SqlScript -ErrorAction Stop
    
    Write-Host "[SUCCESS] View created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Display results
    Write-Host "Verification Results:" -ForegroundColor Yellow
    $Results | Format-Table -AutoSize
    
    Write-Host ""
    Write-Host "[SUCCESS] Your 'Manage Courses' page should now work!" -ForegroundColor Green
    Write-Host "Test it at: https://ai-learning-tracker-bharath.azurewebsites.net" -ForegroundColor Cyan
}
catch {
    Write-Host "[ERROR] Failed to execute SQL script:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Please try manual execution via Azure Portal:" -ForegroundColor Yellow
    Write-Host "1. Go to https://portal.azure.com" -ForegroundColor White
    Write-Host "2. Navigate to ai-learning-rg → ai-learning-db" -ForegroundColor White
    Write-Host "3. Use Query Editor to run the script in azure_sql_fix.sql" -ForegroundColor White
    exit 1
}
finally {
    # Clear password from memory
    if ($PlainPassword) {
        $PlainPassword = $null
    }
}
