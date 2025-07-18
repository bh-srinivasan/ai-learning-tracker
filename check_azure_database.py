#!/usr/bin/env python3
"""
Azure Database User Checker
==========================

This script connects to the Azure database to check user accounts and their status.
"""

import os
import sqlite3
import sys
from datetime import datetime

def check_azure_database():
    """Check Azure database for user accounts"""
    print("=== AZURE DATABASE USER CHECK ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database path (Azure uses ai_learning.db)
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found locally")
        print("Note: This check is for local database. Azure database is separate.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table does not exist")
            print("🔧 Database schema needs to be initialized")
            return False
        
        # Get all users
        cursor.execute("SELECT id, username, email, level, points, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        
        if not users:
            print("⚠️ No users found in database")
            print("🔧 User initialization required")
            return False
        
        print(f"✅ Found {len(users)} users in database:")
        print("-" * 80)
        for user in users:
            user_id, username, email, level, points, created_at = user
            print(f"ID: {user_id:2} | Username: {username:15} | Email: {email:25} | Level: {level:10} | Points: {points:5} | Created: {created_at}")
        
        # Check specifically for admin user
        cursor.execute("SELECT username, email, level FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        print("\n=== ADMIN USER STATUS ===")
        if admin:
            username, email, level = admin
            print(f"✅ Admin user found: {username} ({email}) - Level: {level}")
        else:
            print("❌ Admin user not found")
            print("🔧 Admin user needs to be created")
        
        # Check password hashes (without showing them)
        cursor.execute("SELECT username, CASE WHEN password_hash IS NOT NULL AND password_hash != '' THEN 'SET' ELSE 'NOT SET' END as pwd_status FROM users")
        pwd_status = cursor.fetchall()
        
        print("\n=== PASSWORD STATUS ===")
        for user, status in pwd_status:
            print(f"{user:15}: {status}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_courses_table():
    """Check courses table status"""
    print("\n=== COURSES TABLE CHECK ===")
    
    db_path = 'ai_learning.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if courses table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
        if not cursor.fetchone():
            print("❌ Courses table does not exist")
            return False
        
        # Get course count
        cursor.execute("SELECT COUNT(*) FROM courses")
        count = cursor.fetchone()[0]
        
        print(f"✅ Courses table exists with {count} courses")
        
        if count > 0:
            cursor.execute("SELECT id, title, provider, level FROM courses LIMIT 5")
            courses = cursor.fetchall()
            print("Sample courses:")
            for course in courses:
                print(f"  - {course[1]} ({course[2]}) - {course[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Courses table error: {e}")
        return False

def main():
    """Main check function"""
    print("AI Learning Tracker - Azure Database Check")
    print("=" * 50)
    
    # Check users
    users_ok = check_azure_database()
    
    # Check courses
    courses_ok = check_courses_table()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Users table: {'✅ OK' if users_ok else '❌ ISSUE'}")
    print(f"Courses table: {'✅ OK' if courses_ok else '❌ ISSUE'}")
    
    if not users_ok:
        print("\n🔧 RECOMMENDATIONS:")
        print("1. Run database initialization: python azure_db_initializer.py")
        print("2. Check if Azure environment has proper database setup")
        print("3. Verify admin user creation process")
    
    return users_ok and courses_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
