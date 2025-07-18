#!/usr/bin/env python3
"""
Check database tables for admin functions
"""
import sqlite3
import os

def check_database_tables():
    """Check if all required database tables exist"""
    
    print("🗄️ CHECKING DATABASE TABLES FOR ADMIN FUNCTIONS")
    print("=" * 55)
    
    db_path = "ai_learning.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 EXISTING TABLES:")
        for table in sorted(tables):
            print(f"   ✅ {table}")
        
        # Check required tables for admin functions
        required_tables = [
            'users',           # For admin_users
            'courses',         # For admin_courses
            'course_search_configs',  # For admin_course_configs
            'learning_entries',       # For general functionality
        ]
        
        print(f"\n🎯 REQUIRED TABLES FOR ADMIN FUNCTIONS:")
        missing_tables = []
        
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table}")
                
                # Check table structure
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"      Columns: {', '.join(column_names)}")
                
            else:
                print(f"   ❌ {table} - MISSING")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️  Missing tables might cause admin page errors: {missing_tables}")
        else:
            print(f"\n✅ All required tables exist!")
        
        conn.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database_tables()
