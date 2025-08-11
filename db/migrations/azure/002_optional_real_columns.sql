-- OPTIONAL: Future migration to add real columns to Azure SQL courses table
-- This script shows how to evolve from the compatibility view to real columns
-- 
-- WARNING: Do NOT run this script yet. It's provided for future reference.
--          The app currently works with the view (001_create_view_courses_app.sql)
--          and can continue to do so indefinitely.
--
-- When ready to migrate to real columns (optional future step):
-- 1. Run this script to add the columns
-- 2. Update the view to select the real columns instead of computed ones
-- 3. Test thoroughly before deploying

/*
-- Step 1: Add the missing columns
ALTER TABLE dbo.courses 
ADD duration_hours float NULL;

ALTER TABLE dbo.courses 
ADD category nvarchar(100) NULL;

-- Step 2: Migrate existing data
UPDATE dbo.courses 
SET duration_hours = TRY_CONVERT(float, duration) 
WHERE duration IS NOT NULL;

-- Step 3: Update the view to use real columns (replaces 001_create_view_courses_app.sql)
CREATE OR ALTER VIEW dbo.courses_app AS
SELECT 
    id,
    title,
    description,
    COALESCE(difficulty, level) AS difficulty,
    duration_hours,  -- Now using real column
    url,
    category,        -- Now using real column
    level,
    created_at
FROM dbo.courses;

-- Step 4: Verify migration
SELECT COUNT(*) as total_courses,
       COUNT(duration_hours) as with_duration_hours,
       COUNT(category) as with_category
FROM dbo.courses_app;
*/
