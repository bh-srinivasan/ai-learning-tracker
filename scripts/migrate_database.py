#!/usr/bin/env python3
"""
Database migration script to ensure Azure database has correct schema
"""

import sqlite3
import os

def migrate_database():
    """Migrate database to ensure all required columns exist"""
    db_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
    
    print(f"Migrating database: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Existing tables: {tables}")
    
    # Add missing columns to courses table if they don't exist
    cursor.execute("PRAGMA table_info(courses);")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Courses table columns: {columns}")
    
    migrations_needed = []
    
    if 'is_active' not in columns:
        migrations_needed.append("ALTER TABLE courses ADD COLUMN is_active INTEGER DEFAULT 1;")
    
    if 'is_retired' not in columns:
        migrations_needed.append("ALTER TABLE courses ADD COLUMN is_retired INTEGER DEFAULT 0;")
    
    if 'url_status' not in columns:
        migrations_needed.append("ALTER TABLE courses ADD COLUMN url_status TEXT DEFAULT 'unknown';")
    
    if 'last_url_check' not in columns:
        migrations_needed.append("ALTER TABLE courses ADD COLUMN last_url_check TIMESTAMP;")
    
    print(f"Migrations needed: {len(migrations_needed)}")
    
    for migration in migrations_needed:
        print(f"Executing: {migration}")
        cursor.execute(migration)
    
    # Update all existing courses to be active by default
    cursor.execute("UPDATE courses SET is_active = 1 WHERE is_active IS NULL;")
    cursor.execute("UPDATE courses SET is_retired = 0 WHERE is_retired IS NULL;")
    cursor.execute("UPDATE courses SET url_status = 'unknown' WHERE url_status IS NULL;")
    
    conn.commit()
    
    # Verify final state
    cursor.execute("PRAGMA table_info(courses);")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"Final courses table columns: {final_columns}")
    
    cursor.execute("SELECT COUNT(*) FROM courses;")
    total_courses = cursor.fetchone()[0]
    print(f"Total courses: {total_courses}")
    
    cursor.execute("SELECT COUNT(*) FROM courses WHERE is_active = 1;")
    active_courses = cursor.fetchone()[0]
    print(f"Active courses: {active_courses}")
    
    conn.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_database()
