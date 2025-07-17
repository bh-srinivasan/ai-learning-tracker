#!/usr/bin/env python3
"""
Update database schema to add course status columns
"""
import sqlite3

def update_database():
    conn = sqlite3.connect('ai_learning.db')
    
    # Set default values for all existing courses
    conn.execute("UPDATE courses SET is_active = 1, is_retired = 0, url_status = 'unchecked'")
    conn.commit()
    
    # Verify the update
    result = conn.execute("SELECT COUNT(*) FROM courses WHERE is_active = 1").fetchone()
    print(f"Updated {result[0]} courses to active status")
    
    conn.close()
    print("Database updated successfully!")

if __name__ == "__main__":
    update_database()
