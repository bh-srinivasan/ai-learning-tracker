#!/bin/bash
# Azure SQL Database Fix Script
# Run this to fix the is_admin column issue in Azure SQL Database

echo "==========================="
echo "Azure SQL Database Fix"
echo "==========================="

APP_NAME="ai-learning-tracker-bharath"
RESOURCE_GROUP="ai-learning-rg"

echo "🔍 Getting Azure SQL Database connection details..."

# Get the database server and name from app service connection strings
echo "📋 Retrieving database connection information..."
az webapp config connection-string list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='defaultConnection'].{Name:name,Value:value}" \
  --output table

echo ""
echo "🔧 Executing database fix..."
echo "This will add the is_admin column and set admin privileges"

# Create SQL script
cat << 'EOF' > /tmp/fix_admin.sql
-- Check if is_admin column exists and add if needed
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
)
BEGIN
    ALTER TABLE users ADD is_admin BIT DEFAULT 0;
    PRINT 'Added is_admin column';
END
ELSE
    PRINT 'is_admin column already exists';

-- Set admin user privileges
UPDATE users SET is_admin = 1 WHERE username = 'admin';
PRINT 'Set admin privileges for admin user';

-- Verify the fix
SELECT id, username, is_admin FROM users WHERE username = 'admin';
EOF

echo "📝 SQL script created at /tmp/fix_admin.sql"
echo ""
echo "🚀 Execute this command to apply the database fix:"
echo ""
echo "az sql db execute-sql-script \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --server <your-sql-server-name> \\"
echo "  --database <your-database-name> \\"
echo "  --sql-script /tmp/fix_admin.sql"
echo ""
echo "Or use Azure Portal SQL Query Editor to run the SQL script."
echo ""
echo "📁 SQL script content:"
cat /tmp/fix_admin.sql
