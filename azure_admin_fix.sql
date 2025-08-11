-- Azure SQL Database Admin Fix
-- Add is_admin column and set admin privileges

-- Step 1: Check if is_admin column exists and add if needed
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
)
BEGIN
    ALTER TABLE users ADD is_admin BIT DEFAULT 0;
    PRINT 'Added is_admin column successfully';
END
ELSE
BEGIN
    PRINT 'is_admin column already exists';
END

-- Step 2: Set admin user privileges
UPDATE users SET is_admin = 1 WHERE username = 'admin';
PRINT 'Admin privileges set for admin user';

-- Step 3: Verify the fix
SELECT 
    id,
    username,
    is_admin,
    CASE 
        WHEN is_admin = 1 THEN 'Admin privileges active'
        ELSE 'No admin privileges'
    END as status
FROM users 
WHERE username = 'admin';

PRINT 'Azure SQL admin fix completed!';
