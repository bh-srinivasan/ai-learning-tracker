#!/usr/bin/env python3
"""
Check Level Settings and Implementation Status
"""

import sqlite3
import os

def main():
    db_path = "ai_learning.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("=" * 60)
    print("LEVEL MANAGEMENT SYSTEM - CURRENT STATUS")
    print("=" * 60)
    
    # Check level_settings data
    print("\n🎯 CURRENT LEVEL SETTINGS:")
    level_settings = conn.execute("SELECT * FROM level_settings ORDER BY points_required ASC").fetchall()
    if level_settings:
        for level in level_settings:
            print(f"  • {level['level_name']}: {level['points_required']} points")
    else:
        print("  ❌ No level settings found!")
    
    # Check user_courses completions
    print("\n🎓 USER COURSE COMPLETIONS:")
    completions = conn.execute("""
        SELECT u.username, c.title, c.points, uc.completed, uc.completion_date
        FROM user_courses uc
        JOIN users u ON uc.user_id = u.id
        JOIN courses c ON uc.course_id = c.id
        ORDER BY u.username, uc.completion_date DESC
    """).fetchall()
    
    if completions:
        for completion in completions:
            status = "✅ COMPLETED" if completion['completed'] else "⏳ IN PROGRESS"
            print(f"  • {completion['username']}: {completion['title']} ({completion['points']} pts) - {status}")
    else:
        print("  ❌ No course enrollments found!")
    
    # Identify missing components
    print("\n🔧 MISSING COMPONENTS NEEDED:")
    
    missing_components = []
    
    # Check if points_log table exists
    points_log_exists = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='points_log'
    """).fetchone()
    
    if not points_log_exists:
        missing_components.append("📝 Points Log Table - Track all point transactions")
    
    # Check if we have proper level progression logic
    users_with_points = conn.execute("SELECT * FROM users WHERE points > 0").fetchall()
    for user in users_with_points:
        expected_level = calculate_expected_level(user['points'], level_settings)
        if user['level'] != expected_level:
            missing_components.append(f"⚠️  {user['username']}: Has {user['points']} points but level is {user['level']}, should be {expected_level}")
    
    if missing_components:
        for component in missing_components:
            print(f"  {component}")
    else:
        print("  ✅ All components present!")
    
    conn.close()

def calculate_expected_level(points, level_settings):
    """Calculate what level should be based on points"""
    for level in reversed(level_settings):  # Start from highest
        if points >= level['points_required']:
            return level['level_name']
    return 'Beginner'

if __name__ == "__main__":
    main()
