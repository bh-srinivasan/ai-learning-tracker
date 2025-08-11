-- Azure SQL Database Admin Fix Script
-- Run this script in Azure SQL Database to fix the admin login issue

PRINT 'Starting Azure SQL Admin Fix...';
PRINT '=====================================';

-- Step 1: Check and add is_admin column
PRINT 'Step 1: Checking for is_admin column...';

IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
)
BEGIN
    PRINT 'Adding is_admin column...';
    ALTER TABLE users ADD is_admin BIT DEFAULT 0;
    PRINT '✅ is_admin column added successfully';
END
ELSE
BEGIN
    PRINT '✅ is_admin column already exists';
END

-- Step 2: Set admin user privileges
PRINT '';
PRINT 'Step 2: Setting admin user privileges...';

DECLARE @AdminExists INT;
SELECT @AdminExists = COUNT(*) FROM users WHERE username = 'admin';

IF @AdminExists > 0
BEGIN
    UPDATE users SET is_admin = 1 WHERE username = 'admin';
    PRINT '✅ Admin privileges set for admin user';
END
ELSE
BEGIN
    PRINT '❌ Admin user not found in database';
END

-- Step 3: Verify the fix
PRINT '';
PRINT 'Step 3: Verification Results:';
PRINT '============================';

SELECT 
    id,
    username,
    is_admin,
    CASE 
        WHEN is_admin = 1 THEN '✅ Admin privileges active'
        ELSE '❌ No admin privileges'
    END as status
FROM users 
WHERE username = 'admin';

PRINT '';
PRINT 'Azure SQL Admin Fix Complete!';
PRINT 'Deploy the updated app.py code and test the admin login.';
