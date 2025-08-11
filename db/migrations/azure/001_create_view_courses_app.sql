-- Azure SQL Migration: Create compatibility view for courses
-- This view exposes the schema expected by the Flask app while mapping Azure SQL columns
-- 
-- Usage: Run this script in Azure SQL Database via Azure Portal Query Editor,
--        Azure Data Studio, or sqlcmd
--
-- Purpose: Fixes "Invalid column name 'duration_hours'" error by providing
--          a compatible interface between Azure SQL schema and app expectations

-- Create or replace the courses_app view for application compatibility
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

-- Grant SELECT permission to application user (adjust if needed)
-- GRANT SELECT ON dbo.courses_app TO [your_app_user];

-- Verification query (optional - run after creation)
-- SELECT TOP 5 * FROM dbo.courses_app;
