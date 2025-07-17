#!/usr/bin/env python3
"""
Check database schema and fix production safety guard
"""

import sqlite3
import json

def check_database_schema():
    """Check the actual database schema"""
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Users table schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get sample data
        cursor.execute("SELECT * FROM users LIMIT 5")
        users = cursor.fetchall()
        
        print(f"\nSample users ({len(users)} rows):")
        for user in users:
            print(f"  {user}")
        
        conn.close()
        
        return [col[1] for col in columns]
        
    except Exception as e:
        print(f"Error checking schema: {e}")
        return []

if __name__ == "__main__":
    columns = check_database_schema()
