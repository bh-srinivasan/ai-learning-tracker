#!/usr/bin/env python3
"""
Level Management System Implementation
Create points_log table and implement comprehensive level management
"""

import sqlite3
import os
from datetime import datetime

def setup_points_log_table():
    """Create points_log table to track all point transactions"""
    conn = sqlite3.connect('ai_learning.db')
    
    # Create points_log table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER,
            action TEXT NOT NULL,
            points_change INTEGER NOT NULL,
            points_before INTEGER NOT NULL,
            points_after INTEGER NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    # Create index for better performance
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_points_log_user_id ON points_log(user_id)
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_points_log_created_at ON points_log(created_at)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Points log table created successfully")

def setup_user_level_settings():
    """Add additional fields to users table for level management"""
    conn = sqlite3.connect('ai_learning.db')
    
    # Add level_points field to track points at current level
    try:
        conn.execute('ALTER TABLE users ADD COLUMN level_points INTEGER DEFAULT 0')
        print("✅ Added level_points column to users table")
    except sqlite3.OperationalError:
        print("ℹ️  level_points column already exists")
    
    # Add level_updated_at field
    try:
        conn.execute('ALTER TABLE users ADD COLUMN level_updated_at TIMESTAMP')
        print("✅ Added level_updated_at column to users table")
    except sqlite3.OperationalError:
        print("ℹ️  level_updated_at column already exists")
    
    conn.commit()
    conn.close()

def migrate_existing_data():
    """Migrate existing user data to new level management system"""
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    print("\n📊 MIGRATING EXISTING USER DATA...")
    
    # Get all users
    users = conn.execute("SELECT id, username, points FROM users").fetchall()
    
    for user in users:
        user_id = user['id']
        current_points = user['points'] or 0
        
        # Recalculate points from completed courses
        course_points = conn.execute('''
            SELECT COALESCE(SUM(c.points), 0) as total
            FROM user_courses uc
            JOIN courses c ON uc.course_id = c.id
            WHERE uc.user_id = ? AND uc.completed = 1
        ''', (user_id,)).fetchone()['total']
        
        # Calculate correct level based on course points
        correct_level = calculate_level_from_points(course_points, conn)
        level_points = calculate_level_points(course_points, correct_level, conn)
        
        # Update user record
        conn.execute('''
            UPDATE users 
            SET points = ?, level = ?, level_points = ?, level_updated_at = ?
            WHERE id = ?
        ''', (course_points, correct_level, level_points, datetime.now(), user_id))
        
        # Create initial points log entry if points > 0
        if course_points > 0:
            conn.execute('''
                INSERT INTO points_log (user_id, action, points_change, points_before, points_after, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, 'MIGRATION', course_points, 0, course_points, 'Initial data migration'))
        
        print(f"  • {user['username']}: {current_points} → {course_points} points, Level: {correct_level}")
    
    conn.commit()
    conn.close()
    print("✅ Data migration completed")

def calculate_level_from_points(total_points, conn):
    """Calculate user level based on total points"""
    level_settings = conn.execute('''
        SELECT level_name, points_required 
        FROM level_settings 
        ORDER BY points_required DESC
    ''').fetchall()
    
    for level in level_settings:
        if total_points >= level['points_required']:
            return level['level_name']
    
    return 'Beginner'

def calculate_level_points(total_points, current_level, conn):
    """Calculate points at current level (points above level threshold)"""
    level_threshold = conn.execute('''
        SELECT points_required 
        FROM level_settings 
        WHERE level_name = ?
    ''', (current_level,)).fetchone()
    
    if level_threshold:
        return total_points - level_threshold['points_required']
    return total_points

def main():
    print("=" * 60)
    print("LEVEL MANAGEMENT SYSTEM - SETUP & MIGRATION")
    print("=" * 60)
    
    # Step 1: Create points_log table
    print("\n🔧 SETTING UP POINTS LOG TABLE...")
    setup_points_log_table()
    
    # Step 2: Add level management fields
    print("\n🔧 SETTING UP USER LEVEL FIELDS...")
    setup_user_level_settings()
    
    # Step 3: Migrate existing data
    print("\n🔄 MIGRATING EXISTING DATA...")
    migrate_existing_data()
    
    print("\n" + "=" * 60)
    print("✅ LEVEL MANAGEMENT SYSTEM SETUP COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
