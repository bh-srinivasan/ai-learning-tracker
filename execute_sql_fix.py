#!/usr/bin/env python3
"""
Execute Azure SQL Fix Script
Automatically runs the SQL script to create the missing courses_app view
"""

import os
import pyodbc
import sys

def execute_sql_fix():
    """Execute the SQL script to fix the courses_app view"""
    
    # Environment variables (same as we tested before)
    server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
    database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
    username = os.environ.get('AZURE_SQL_USERNAME', 'sqladmin')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    if not password:
        print("❌ Error: AZURE_SQL_PASSWORD environment variable not set")
        print("Please run: $env:AZURE_SQL_PASSWORD='your_password'")
        return False
    
    # Connection string
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    
    # SQL Script to execute
    sql_script = """
-- AZURE SQL FIX: Create Missing Compatibility View
-- This resolves the "Invalid object name 'dbo.courses_app'" error

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

-- Step 2: Verify the view works
SELECT TOP 5 
    id, 
    title, 
    difficulty, 
    duration_hours,
    category
FROM dbo.courses_app 
ORDER BY created_at DESC;
"""
    
    try:
        print("🔄 Connecting to Azure SQL Database...")
        print(f"Server: {server}")
        print(f"Database: {database}")
        print(f"Username: {username}")
        
        # Connect to database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        
        # Execute the SQL script
        print("🔄 Executing SQL script to create courses_app view...")
        
        # Split script into individual statements
        statements = sql_script.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                print(f"Executing: {statement[:50]}...")
                cursor.execute(statement)
        
        # Commit the changes
        conn.commit()
        
        print("✅ SQL script executed successfully!")
        print("✅ courses_app view created!")
        
        # Verify by selecting from the view
        print("\n🔍 Verifying the view works...")
        cursor.execute("SELECT COUNT(*) as course_count FROM dbo.courses_app")
        result = cursor.fetchone()
        print(f"✅ courses_app view contains {result[0]} courses")
        
        # Show sample data
        cursor.execute("SELECT TOP 3 id, title, difficulty FROM dbo.courses_app ORDER BY created_at DESC")
        rows = cursor.fetchall()
        print("\n📋 Sample data from courses_app view:")
        for row in rows:
            print(f"  ID: {row[0]}, Title: {row[1]}, Difficulty: {row[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 SUCCESS: Azure SQL fix completed!")
        print("Your 'Manage Courses' page should now work without errors.")
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== Azure SQL Fix Script ===")
    success = execute_sql_fix()
    sys.exit(0 if success else 1)
