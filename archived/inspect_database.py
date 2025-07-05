#!/usr/bin/env python3
"""
Database Schema Inspector
Check the current database schema and identify missing columns
"""

import sqlite3
import os
from dotenv import load_dotenv

def inspect_database_schema():
    """Inspect the current database schema"""
    load_dotenv()
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        print("🔍 AI Learning Tracker - Database Schema Inspector")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        print("\n" + "=" * 60)
        
        # Inspect each table
        for table in tables:
            table_name = table[0]
            print(f"\n📊 Table: {table_name}")
            print("-" * 30)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                col_id, name, type_name, not_null, default, pk = col
                null_str = "NOT NULL" if not_null else "NULL"
                pk_str = "PRIMARY KEY" if pk else ""
                default_str = f"DEFAULT {default}" if default else ""
                print(f"   {col_id}: {name} ({type_name}) {null_str} {pk_str} {default_str}".strip())
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Special inspection for courses table
            if table_name == 'courses':
                print("\n🔍 Courses Table Detailed Analysis:")
                cursor.execute("SELECT * FROM courses LIMIT 3;")
                sample_rows = cursor.fetchall()
                if sample_rows:
                    print("Sample data:")
                    for i, row in enumerate(sample_rows):
                        print(f"   Row {i+1}: {row}")
                else:
                    print("   No data found")
            
            # Special inspection for learnings table
            if 'learning' in table_name.lower():
                print(f"\n🔍 {table_name} Table Analysis:")
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id IS NULL OR user_id = '';")
                global_count = cursor.fetchone()[0]
                print(f"   Global entries (no user_id): {global_count}")
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id IS NOT NULL AND user_id != '';")
                user_count = cursor.fetchone()[0]
                print(f"   User-specific entries: {user_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

def check_missing_columns():
    """Check for specific missing columns that might cause issues"""
    print("\n🔧 Checking for Missing Columns")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check courses table for url column
        cursor.execute("PRAGMA table_info(courses);")
        courses_columns = [col[1] for col in cursor.fetchall()]
        
        print("📋 Courses table columns:")
        print(f"   {', '.join(courses_columns)}")
        
        if 'url' not in courses_columns:
            print("❌ Missing 'url' column in courses table!")
            print("💡 This explains the LinkedIn course add error")
        else:
            print("✅ 'url' column exists in courses table")
        
        # Check for other potentially missing columns
        expected_columns = ['id', 'title', 'description', 'category', 'difficulty', 'url', 'created_at']
        missing_columns = [col for col in expected_columns if col not in courses_columns]
        
        if missing_columns:
            print(f"⚠️  Potentially missing columns: {', '.join(missing_columns)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking columns: {e}")

if __name__ == "__main__":
    inspect_database_schema()
    check_missing_columns()
