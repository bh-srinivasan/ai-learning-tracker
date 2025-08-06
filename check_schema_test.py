#!/usr/bin/env python3
"""Check database schema"""

import sqlite3

def check_schema():
    """Check the current database schema"""
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Get all table names
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        print("Database Tables:")
        for table in tables:
            print(f"- {table['name']}")
        
        # Check users table schema
        if any(table['name'] == 'users' for table in tables):
            print("\nUsers table schema:")
            schema = conn.execute("PRAGMA table_info(users)").fetchall()
            for column in schema:
                print(f"  {column['name']} ({column['type']})")
        
    except Exception as e:
        print(f"Error checking schema: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_schema()
