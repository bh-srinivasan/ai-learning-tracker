#!/usr/bin/env python3
"""
Database Schema Inspector
Check current database structure for users, levels, and points
"""

import sqlite3
import os

def main():
    db_path = "ai_learning.db"
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("=" * 60)
    print("DATABASE SCHEMA INSPECTION")
    print("=" * 60)
    
    # Get all tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"\n📋 TABLES FOUND: {len(tables)}")
    for table in tables:
        print(f"  • {table['name']}")
    
    # Check if level_settings table exists
    level_settings_exists = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='level_settings'
    """).fetchone()
    
    print(f"\n🎯 LEVEL SETTINGS TABLE: {'✅ EXISTS' if level_settings_exists else '❌ MISSING'}")
    
    # Check users table schema
    print("\n👤 USERS TABLE SCHEMA:")
    users_schema = conn.execute("PRAGMA table_info(users)").fetchall()
    for col in users_schema:
        print(f"  • {col['name']}: {col['type']} {'(PRIMARY KEY)' if col['pk'] else ''}")
    
    # Check current users and their data
    print("\n📊 CURRENT USERS DATA:")
    users = conn.execute("SELECT id, username, level, points, user_selected_level FROM users").fetchall()
    for user in users:
        selected_level = user['user_selected_level'] if user['user_selected_level'] else 'N/A'
        print(f"  • {user['username']}: Level={user['level']}, Points={user['points']}, Selected={selected_level}")
    
    # Check if points_log table exists
    points_log_exists = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='points_log'
    """).fetchone()
    
    print(f"\n📝 POINTS LOG TABLE: {'✅ EXISTS' if points_log_exists else '❌ MISSING'}")
    
    # Check courses table
    print("\n📚 COURSES TABLE SCHEMA:")
    courses_schema = conn.execute("PRAGMA table_info(courses)").fetchall()
    for col in courses_schema:
        print(f"  • {col['name']}: {col['type']}")
    
    # Check user_courses table
    user_courses_exists = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='user_courses'
    """).fetchone()
    
    print(f"\n🎓 USER_COURSES TABLE: {'✅ EXISTS' if user_courses_exists else '❌ MISSING'}")
    
    if user_courses_exists:
        user_courses_schema = conn.execute("PRAGMA table_info(user_courses)").fetchall()
        for col in user_courses_schema:
            print(f"  • {col['name']}: {col['type']}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("SCHEMA INSPECTION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
