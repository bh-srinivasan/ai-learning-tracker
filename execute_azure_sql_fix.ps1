# Azure SQL Database Fix Execution
# This script will execute the SQL fix for the is_admin column

# Get credentials from environment variables
$server = $env:AZURE_SQL_SERVER
if (-not $server) { $server = "ai-learning-sql-centralus.database.windows.net" }

$database = $env:AZURE_SQL_DATABASE  
if (-not $database) { $database = "ai-learning-db" }

$username = $env:AZURE_SQL_USERNAME
if (-not $username) { $username = "ailearningadmin" }

$password = $env:AZURE_SQL_PASSWORD
if (-not $password) {
    Write-Host "❌ ERROR: AZURE_SQL_PASSWORD environment variable is required!" -ForegroundColor Red
    Write-Host "Please set it using: `$env:AZURE_SQL_PASSWORD = 'your_password'" -ForegroundColor Yellow
    exit 1
}

$sqlFile = "azure_admin_fix.sql"

Write-Host "==========================="
Write-Host "Azure SQL Database Fix"
Write-Host "==========================="

Write-Host "🔗 Connecting to Azure SQL Database..."
Write-Host "   Server: $server"
Write-Host "   Database: $database"
Write-Host "   Username: $username"

# Check if sqlcmd is available
if (!(Get-Command "sqlcmd" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ sqlcmd not found. Installing SQL Server Command Line Utilities..."
    Write-Host "Please install SQL Server Command Line Utilities from:"
    Write-Host "https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility"
    exit 1
}

Write-Host "✅ sqlcmd found"

# Execute the SQL fix
Write-Host "🔧 Executing SQL fix..."
try {
    sqlcmd -S $server -d $database -U $username -P $password -i $sqlFile -o azure_sql_output.txt
    
    Write-Host "✅ SQL fix executed successfully!"
    Write-Host "📋 Output:"
    Get-Content azure_sql_output.txt
}
catch {
    Write-Host "❌ Error executing SQL fix: $_"
    exit 1
}

Write-Host ""
Write-Host "🎉 Azure SQL Database fix completed!"
Write-Host "Now test the admin login in the application."
