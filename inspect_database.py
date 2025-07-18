#!/usr/bin/env python3
"""
Database Schema Inspector
========================

Check the actual database schema to understand the table structure.
"""

import sqlite3
import os

def inspect_database_schema():
    """Inspect the actual database schema"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("=== DATABASE SCHEMA INSPECTION ===")
        print(f"Database: {db_path}")
        print(f"Tables found: {len(tables)}")
        print()
        
        for table_name in tables:
            table = table_name[0]
            print(f"TABLE: {table}")
            print("-" * 40)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, name, data_type, not_null, default_val, pk = col
                pk_marker = " (PRIMARY KEY)" if pk else ""
                null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default_val}" if default_val else ""
                print(f"  {name}: {data_type}{pk_marker}{null_marker}{default_marker}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
            
            # Show sample data if users table
            if table == 'users' and count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                print("  Sample data:")
                for row in rows:
                    print(f"    {row}")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_database_schema()
