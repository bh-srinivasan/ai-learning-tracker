-- AZURE SQL FIX: Create Missing Compatibility View
-- 
-- EXECUTE THIS IN AZURE PORTAL QUERY EDITOR
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
