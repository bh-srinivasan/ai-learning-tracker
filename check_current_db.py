#!/usr/bin/env python3
"""
Check database schema and current users
"""

import sqlite3
import os

def check_database():
    """Check the database schema and current data."""
    
    db_path = 'ai_learning.db'
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get users table schema
    print("📋 USERS TABLE SCHEMA:")
    print("-" * 30)
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    
    # Get current users
    print(f"\n👥 CURRENT USERS:")
    print("-" * 30)
    cursor.execute("SELECT * FROM users ORDER BY id")
    users = cursor.fetchall()
    
    if users:
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  {user}")
    else:
        print("❌ NO USERS FOUND IN DATABASE!")
    
    # Get all table names
    print(f"\n📊 ALL TABLES:")
    print("-" * 30)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  {table[0]}: {count} records")
    
    conn.close()

if __name__ == "__main__":
    check_database()
