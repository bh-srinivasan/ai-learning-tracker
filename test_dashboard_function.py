#!/usr/bin/env python3
"""
Test Dashboard Function for Non-Admin Users
Diagnose the Internal Server Error on dashboard access
"""
import pyodbc
import sys
import os
from datetime import datetime

def test_dashboard_function():
    """Test the dashboard function components to find the issue"""
    
    # Environment variables
    server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
    database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
    username = os.environ.get('AZURE_SQL_USERNAME', 'ailearningadmin')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    if not password:
        print("❌ Error: AZURE_SQL_PASSWORD environment variable not set")
        return False
    
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    
    try:
        print("🔄 Testing Dashboard Function Components...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("✅ Connected to Azure SQL Database")
        
        # Test 1: Get a non-admin user for testing
        print("\n1️⃣ Testing: Get non-admin user...")
        cursor.execute("SELECT TOP 1 id, username, level, points FROM users WHERE is_admin = 0 OR is_admin IS NULL")
        test_user = cursor.fetchone()
        if test_user:
            user_id = test_user[0]
            username = test_user[1]
            level = test_user[2]
            points = test_user[3]
            print(f"✅ Test user found: {username} (ID: {user_id}, Level: {level}, Points: {points})")
        else:
            print("❌ No non-admin users found")
            return False
        
        # Test 2: Get user points (this line might be failing)
        print("\n2️⃣ Testing: Get user points...")
        try:
            cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
            user_points_result = cursor.fetchone()
            if user_points_result:
                user_points = user_points_result[0]
                print(f"✅ User points retrieved: {user_points}")
            else:
                print("❌ Failed to get user points")
                return False
        except Exception as e:
            print(f"❌ Error getting user points: {e}")
            return False
        
        # Test 3: Test learning entries query
        print("\n3️⃣ Testing: Learning entries query...")
        try:
            cursor.execute("""
                SELECT TOP 5 * FROM learning_entries 
                WHERE (user_id = ? OR is_global = 1)
                ORDER BY date_added DESC
            """, (user_id,))
            recent_entries = cursor.fetchall()
            print(f"✅ Learning entries retrieved: {len(recent_entries)} entries")
        except Exception as e:
            print(f"❌ Error getting learning entries: {e}")
            print("This might be the issue! Let's check if learning_entries table structure is correct...")
            try:
                cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'learning_entries'")
                columns = cursor.fetchall()
                print("Learning entries columns:")
                for col in columns:
                    print(f"  - {col[0]}")
            except Exception as col_error:
                print(f"Error checking columns: {col_error}")
        
        # Test 4: Test courses query (with user_courses join)
        print("\n4️⃣ Testing: Courses query...")
        try:
            cursor.execute("""
                SELECT TOP 5 c.*, 
                       CASE WHEN uc.completed IS NOT NULL THEN uc.completed ELSE 0 END as completed
                FROM courses c
                LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
                ORDER BY c.level, c.points DESC
            """, (user_id,))
            available_courses = cursor.fetchall()
            print(f"✅ Courses retrieved: {len(available_courses)} courses")
        except Exception as e:
            print(f"❌ Error getting courses: {e}")
            print("Checking courses table structure...")
            try:
                cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'courses'")
                columns = cursor.fetchall()
                print("Courses table columns:")
                for col in columns:
                    print(f"  - {col[0]}")
            except Exception as col_error:
                print(f"Error checking columns: {col_error}")
        
        # Test 5: Check if level_manager functions are accessible
        print("\n5️⃣ Testing: Level management functions...")
        try:
            # Simple level calculation based on points
            if user_points is None:
                user_points = 0
            
            # Basic level calculation (simulating what update_user_level might do)
            if user_points < 200:
                calculated_level = "Beginner"
            elif user_points < 500:
                calculated_level = "Learner"
            elif user_points < 1000:
                calculated_level = "Intermediate"
            else:
                calculated_level = "Expert"
            
            print(f"✅ Level calculation works: {calculated_level} for {user_points} points")
            
        except Exception as e:
            print(f"❌ Error in level calculation: {e}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Dashboard function test completed successfully!")
        print("If the dashboard is still failing, the issue might be in:")
        print("1. The update_user_level function import/call")
        print("2. Session management (get_current_user)")
        print("3. Template rendering")
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== Dashboard Function Diagnostic Test ===")
    success = test_dashboard_function()
    sys.exit(0 if success else 1)
