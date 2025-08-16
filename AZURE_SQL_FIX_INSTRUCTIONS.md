# AZURE SQL FIX - Manual Execution Guide

## Problem
Your app is getting this error when clicking "Manage Courses":
```
Error loading courses: ('42S02', "[42S02] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Invalid object name 'dbo.courses_app'. (208) (SQLExecDirectW)")
```

## Solution
Execute the SQL script to create the missing `dbo.courses_app` view.

## Step-by-Step Instructions

### Option 1: Azure Portal (Recommended)

1. **Open Azure Portal**: Go to https://portal.azure.com

2. **Navigate to SQL Database**:
   - Go to Resource Groups → `ai-learning-rg`
   - Click on SQL Database → `ai-learning-db`
   - Server: `ai-learning-sql-centralus`

3. **Open Query Editor**:
   - In the left menu, click "Query editor (preview)"
   - Sign in with your SQL credentials

4. **Execute the SQL Script**:
   Copy and paste this entire script into the query editor:

```sql
-- AZURE SQL FIX: Create Missing Compatibility View
-- 
-- This resolves the "Invalid object name 'dbo.courses_app'" error
-- by creating the compatibility view your application expects.

-- Step 1: Create the compatibility view
CREATE OR ALTER VIEW dbo.courses_app AS
SELECT 
    id,
    title,
    description,
    COALESCE(difficulty, level) AS difficulty,  -- Use difficulty if available, fallback to level
    TRY_CONVERT(float, duration) AS duration_hours,  -- Convert duration string to float
    url,
    CAST(NULL AS nvarchar(100)) AS category,  -- Placeholder for missing category column
    level,
    created_at
FROM dbo.courses;

-- Step 2: Verify the view works (optional)
SELECT TOP 5 
    id, 
    title, 
    difficulty, 
    duration_hours,
    category
FROM dbo.courses_app 
ORDER BY created_at DESC;

-- Success message
PRINT 'SUCCESS: dbo.courses_app view created successfully!';
PRINT 'Your Admin Courses page should now work without errors.';
```

5. **Click "Run"** to execute the script

6. **Expected Result**: You should see:
   - "Commands completed successfully" message
   - Sample data from the courses_app view
   - Success messages

### Option 2: Azure Data Studio (Alternative)

1. Download and install Azure Data Studio
2. Connect to: `ai-learning-sql-centralus.database.windows.net`
3. Database: `ai-learning-db`
4. Execute the same SQL script above

### Option 3: Command Line (Alternative)

If you have sqlcmd installed:
```bash
sqlcmd -S ai-learning-sql-centralus.database.windows.net -d ai-learning-db -U [username] -P [password] -i azure_sql_fix.sql
```

## Verification

After running the script:

1. **Test the App**: Go to your Azure app and click "Manage Courses"
2. **Expected Result**: The page should load without the error
3. **You should see**: The courses management interface

## What This Script Does

- **Creates a VIEW** called `dbo.courses_app` that your Flask application expects
- **Maps Azure SQL columns** to the schema your app needs
- **Handles data type conversions** (e.g., duration string → float)
- **Provides compatibility** without changing your application code

## Azure Database Details

- **Resource Group**: ai-learning-rg
- **SQL Server**: ai-learning-sql-centralus
- **Database**: ai-learning-db
- **Status**: Online ✅

## Next Steps

After successful execution:
1. Test the "Manage Courses" functionality
2. Verify courses can be viewed and managed
3. The error should be completely resolved

## Support

If you encounter any issues:
1. Check the Azure Portal for any error messages
2. Verify you're connected to the correct database
3. Ensure you have sufficient permissions to create views

---
**File**: AZURE_SQL_FIX_INSTRUCTIONS.md
**Created**: August 12, 2025
**Purpose**: Resolve courses_app table missing error in Azure
