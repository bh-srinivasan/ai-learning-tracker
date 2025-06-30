#!/usr/bin/env python3
"""
Fix user level inconsistencies in the database
"""

import sqlite3
from level_manager import LevelManager

def fix_user_levels():
    print("="*60)
    print("FIXING USER LEVEL INCONSISTENCIES")
    print("="*60)
    
    # Initialize level manager
    level_manager = LevelManager()
    
    # Get database connection
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Get all users
    users = conn.execute("SELECT id, username, level, points FROM users").fetchall()
    
    print("\n🔧 CHECKING AND FIXING USER LEVELS:")
    print("-" * 40)
    
    for user in users:
        user_id = user['id']
        current_level = user['level']
        current_points = user['points']
        
        # Calculate what the level should be
        correct_level = level_manager.calculate_level_from_points(current_points)
        
        print(f"\n👤 {user['username']} (ID: {user_id})")
        print(f"   Current: {current_level} with {current_points} points")
        print(f"   Should be: {correct_level}")
        
        if current_level != correct_level:
            print(f"   ❌ INCONSISTENT - Fixing...")
            
            # Update user points and level properly
            new_level, total_points, level_points = level_manager.update_user_points_from_courses(user_id)
            
            print(f"   ✅ FIXED: {new_level} with {total_points} points ({level_points} at level)")
        else:
            print(f"   ✅ CONSISTENT")
    
    conn.close()
    
    print("\n" + "="*60)
    print("USER LEVEL FIXES COMPLETED")
    print("="*60)

if __name__ == "__main__":
    fix_user_levels()
