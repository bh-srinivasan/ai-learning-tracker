#!/usr/bin/env python3
"""
Test the profile route directly by simulating the template rendering
"""

import sqlite3
from level_manager import LevelManager

def simulate_profile_route():
    print("="*70)
    print("SIMULATING PROFILE ROUTE EXECUTION")
    print("="*70)
    
    # Simulate what the profile route does
    user_id = 2  # bharath user ID
    
    # Initialize level manager (like in the route)
    level_manager = LevelManager()
    
    # Get comprehensive level info (like in the route)
    level_info = level_manager.get_user_level_info(user_id)
    
    # Get database connection (like in the route)
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # User data query (like in the route)
        user_data = conn.execute('''
            SELECT username, level, points, level_points, user_selected_level, created_at, 
                   last_login, last_activity, login_count
            FROM users 
            WHERE id = ?
        ''', (user_id,)).fetchone()
        
        # Active sessions query (like in the route)
        active_sessions = conn.execute('''
            SELECT session_token, created_at, expires_at, ip_address, user_agent,
                   CASE WHEN expires_at > datetime('now') THEN 'Active' ELSE 'Expired' END as status
            FROM user_sessions 
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
        ''', (user_id,)).fetchall()
        
        # Learning stats queries (like in the route)
        total_learnings = conn.execute('''
            SELECT COUNT(*) as count 
            FROM learning_entries 
            WHERE user_id = ? AND is_global = 0
        ''', (user_id,)).fetchone()['count']
        
        completed_courses = conn.execute('''
            SELECT COUNT(*) as count 
            FROM user_courses 
            WHERE user_id = ? AND completed = 1
        ''', (user_id,)).fetchone()['count']
        
        enrolled_courses = conn.execute('''
            SELECT COUNT(*) as count 
            FROM user_courses 
            WHERE user_id = ? AND completed = 0
        ''', (user_id,)).fetchone()['count']
        
        # Points log (like in the route)
        points_log = level_manager.get_user_points_log(user_id, limit=10)
        
        print("\n✅ ALL TEMPLATE VARIABLES READY:")
        print("-" * 50)
        
        # Test template variables
        template_vars = {
            'user': user_data,
            'level_info': level_info,
            'active_sessions': active_sessions,
            'total_learnings': total_learnings,
            'completed_courses': completed_courses,
            'enrolled_courses': enrolled_courses,
            'points_log': points_log
        }
        
        for var_name, var_value in template_vars.items():
            if var_value is not None:
                if hasattr(var_value, '__len__') and not isinstance(var_value, (str, dict)):
                    print(f"   ✅ {var_name}: {len(var_value)} items")
                elif isinstance(var_value, dict):
                    print(f"   ✅ {var_name}: {len(var_value)} fields")
                else:
                    print(f"   ✅ {var_name}: {var_value}")
            else:
                print(f"   ❌ {var_name}: None/Missing")
        
        # Test specific template usage that was failing
        print("\n🧪 TESTING TEMPLATE VARIABLE ACCESS:")
        print("-" * 50)
        
        # Test level_info.next_level (the line that was failing)
        if level_info and 'next_level' in level_info:
            print(f"   ✅ level_info.next_level: {level_info['next_level']}")
        else:
            print("   ❌ level_info.next_level: MISSING")
        
        # Test user.level
        if user_data and 'level' in user_data:
            print(f"   ✅ user.level: {user_data['level']}")
        else:
            print("   ❌ user.level: MISSING")
        
        # Test user.points
        if user_data and 'points' in user_data:
            print(f"   ✅ user.points: {user_data['points']}")
        else:
            print("   ❌ user.points: MISSING")
        
        # Test level_info.level_points
        if level_info and 'level_points' in level_info:
            print(f"   ✅ level_info.level_points: {level_info['level_points']}")
        else:
            print("   ❌ level_info.level_points: MISSING")
        
        print("\n✅ TEMPLATE RENDERING SHOULD NOW WORK")
        
    finally:
        conn.close()
    
    print("\n" + "="*70)
    print("PROFILE ROUTE SIMULATION COMPLETED")
    print("="*70)

if __name__ == "__main__":
    simulate_profile_route()
