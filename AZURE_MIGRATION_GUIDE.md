# 🛠️ Azure Course Migration Setup & Usage Guide

## Overview
This migration script safely transfers your course database from local SQLite to Azure SQL Database. It includes comprehensive safeguards to prevent accidental re-execution and data corruption.

## ⚠️ IMPORTANT WARNINGS

1. **ONE-TIME OPERATION**: This script can only be run once successfully
2. **IRREVERSIBLE**: Once completed, the migration cannot be undone automatically
3. **TEST FIRST**: Always run with `--dry-run` before live migration
4. **BACKUP**: Ensure you have backups of both local and Azure databases

## 📋 Prerequisites

### 1. Install Required Dependencies
```bash
pip install pyodbc python-dotenv
```

### 2. Configure Azure SQL Database
- Ensure your Azure SQL Database is created and accessible
- Configure firewall rules to allow your IP address
- Create the `courses` table with the same schema as your local database

### 3. Set Up Environment Variables
```bash
# Copy the template
cp .env.azure.template .env.azure

# Edit the file with your actual Azure SQL credentials
notepad .env.azure
```

Required environment variables:
- `AZURE_SQL_SERVER`: Your Azure SQL server name (e.g., myserver.database.windows.net)
- `AZURE_SQL_DATABASE`: Your database name
- `AZURE_SQL_USERNAME`: Your username
- `AZURE_SQL_PASSWORD`: Your password

## 🚀 Usage

### Step 1: Dry Run (ALWAYS DO THIS FIRST)
```bash
python migrate_courses_to_azure.py --dry-run
```

This will:
- Test all connections
- Validate all course data
- Show exactly what would be migrated
- Identify any issues before actual migration

### Step 2: Live Migration (ONLY AFTER SUCCESSFUL DRY RUN)
```bash
python migrate_courses_to_azure.py
```

You will be prompted to type 'MIGRATE' to confirm.

## 🔒 Built-in Safeguards

### Migration Tracking
- Creates `migration_metadata.json` to track completion
- Refuses to run if migration was already completed
- Stores detailed statistics and timestamps

### Data Validation
- Validates all required fields (title, URL, source, level)
- Ensures valid point values and levels
- Skips malformed or incomplete records

### Duplicate Prevention
- Checks for existing courses in Azure before inserting
- Uses title+URL hash for duplicate detection
- Logs all skipped duplicates

### Error Handling
- Transaction-based atomic operations
- Detailed error logging for debugging
- Graceful rollback on failures

## 📊 Expected Output

### Dry Run Example:
```
🛠️  One-Time Course Database Migration: Local → Azure
============================================================
🔄 RUNNING IN DRY-RUN MODE
   No actual changes will be made to Azure database
   This is safe for testing and validation
============================================================
🚀 Starting Course Database Migration
📋 Mode: DRY RUN
🔄 Step 1: Testing Azure SQL connection...
⚠️  Missing Azure SQL env vars (OK for dry-run): ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE']
🔄 DRY RUN: Skipping Azure SQL connection test
🔄 Step 2: Reading local course database...
📂 Reading courses from local database: ai_learning.db
📊 Found 56 raw course records
✅ Validated 56 courses
🔄 Step 3: Checking for existing courses in Azure...
🔄 DRY RUN: Returning empty course hash set
🔄 Step 4: Migrating courses to Azure...
🔄 DRY RUN: Would process 56 courses
🔄 DRY RUN Results: {'total_processed': 56, 'inserted': 56, 'skipped_duplicates': 0, 'failed': 0}
🎉 MIGRATION COMPLETED SUCCESSFULLY!
📊 Final Statistics:
   Total Courses Processed: 56
   Successfully Inserted: 56
   Skipped (Duplicates): 0
   Failed: 0

✅ Migration process completed successfully!
💡 Run without --dry-run to perform actual migration
```

### Live Migration Example:
```
🛠️  One-Time Course Database Migration: Local → Azure
============================================================
⚠️  LIVE MIGRATION MODE
   This will make permanent changes to Azure database
   Ensure you have tested with --dry-run first

Do you want to proceed? (type 'MIGRATE' to confirm): MIGRATE
============================================================
🚀 Starting Course Database Migration
📋 Mode: LIVE MIGRATION
🔄 Step 1: Testing Azure SQL connection...
✅ Azure SQL connection successful
🔄 Step 2: Reading local course database...
📂 Reading courses from local database: ai_learning.db
📊 Found 56 raw course records
✅ Validated 56 courses
🔄 Step 3: Checking for existing courses in Azure...
📊 Found 0 existing courses in Azure database
🔄 Step 4: Migrating courses to Azure...
✅ Inserted: Microsoft 365 Fundamentals... (80 pts, Beginner)
✅ Inserted: Machine Learning with Python: Foundation... (180 pts, Intermediate)
... (continues for all courses)
📊 Migration completed: {'total_processed': 56, 'inserted': 56, 'skipped_duplicates': 0, 'failed': 0}
🔄 Step 5: Updating migration metadata...
✅ Migration metadata saved to migration_metadata.json
🎉 MIGRATION COMPLETED SUCCESSFULLY!
📊 Final Statistics:
   Total Courses Processed: 56
   Successfully Inserted: 56
   Skipped (Duplicates): 0
   Failed: 0
🔒 Migration tracking enabled - script will refuse to run again

✅ Migration process completed successfully!
🔒 Migration tracking activated - script protected from re-execution
```

## 🔧 Troubleshooting

### Common Issues:

1. **pyodbc ImportError**
   ```bash
   pip install pyodbc
   ```

2. **Azure SQL Connection Failed**
   - Check firewall rules
   - Verify server name and credentials
   - Ensure database exists

3. **Migration Already Completed**
   - Script refuses to run after successful completion
   - Delete `migration_metadata.json` only if you're certain you need to re-run

4. **Missing Environment Variables**
   - Ensure `.env.azure` file exists and contains all required variables
   - Load environment variables: `source .env.azure` (Linux/Mac) or set them in PowerShell

### Logs and Debugging:
- Check the generated log file: `migration_YYYYMMDD_HHMMSS.log`
- All operations are logged with timestamps
- Includes detailed error messages for debugging

## 🔄 Post-Migration

### Verification Steps:
1. Check Azure SQL Database for all migrated courses
2. Verify course counts match between local and Azure
3. Test your application with the Azure database
4. Keep `migration_metadata.json` for audit purposes

### Cleanup (Optional):
- Archive the migration script after successful completion
- Secure or rotate Azure SQL credentials
- Document the migration in your deployment notes

## 🆘 Emergency Procedures

### If Migration Fails Halfway:
1. Check the log file for specific error details
2. Fix the underlying issue (connectivity, permissions, etc.)
3. The script is designed to be idempotent - it will skip already-migrated courses
4. Delete `migration_metadata.json` only if you need to restart completely

### If You Need to Re-run:
1. **CAUTION**: Only do this if the migration truly failed
2. Delete `migration_metadata.json`
3. Optionally clean up any partial data in Azure
4. Run dry-run first to verify everything is working
5. Run live migration again

## 📞 Support
If you encounter issues not covered here:
1. Check the detailed log files
2. Verify all prerequisites are met
3. Test with --dry-run to isolate the problem
4. Review Azure SQL Database connectivity and permissions
