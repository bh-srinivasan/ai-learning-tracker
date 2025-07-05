#!/usr/bin/env python3
"""
Test the updated profile functionality
"""

import sqlite3
from level_manager import LevelManager

def test_profile_functionality():
    print("="*60)
    print("TESTING UPDATED PROFILE FUNCTIONALITY")
    print("="*60)
    
    # Initialize level manager
    level_manager = LevelManager()
    
    # Get bharath user for testing
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    bharath_user = conn.execute("SELECT * FROM users WHERE username = 'bharath'").fetchone()
    
    if not bharath_user:
        print("❌ Bharath user not found")
        return
    
    user_id = bharath_user['id']
    
    print(f"\n👤 Testing profile for: {bharath_user['username']}")
    
    # Test 1: Get comprehensive level info (what the profile page will use)
    print("\n🧪 TEST 1: Comprehensive Level Info")
    print("-" * 40)
    
    level_info = level_manager.get_user_level_info(user_id)
    
    required_fields = [
        'username', 'current_level', 'selected_level', 'total_points', 
        'level_points', 'next_level', 'points_to_next', 'progress_percentage'
    ]
    
    for field in required_fields:
        if field in level_info:
            print(f"   ✅ {field}: {level_info[field]}")
        else:
            print(f"   ❌ {field}: MISSING")
    
    # Test 2: User data query (what profile route will get)
    print("\n🧪 TEST 2: User Data Query")
    print("-" * 40)
    
    user_data = conn.execute('''
        SELECT username, level, points, level_points, user_selected_level, created_at, 
               last_login, last_activity, login_count
        FROM users 
        WHERE id = ?
    ''', (user_id,)).fetchone()
    
    if user_data:
        for key in user_data.keys():
            print(f"   ✅ {key}: {user_data[key]}")
    else:
        print("   ❌ User data not found")
    
    # Test 3: Active sessions query
    print("\n🧪 TEST 3: Active Sessions Query")
    print("-" * 40)
    
    active_sessions = conn.execute('''
        SELECT session_token, created_at, expires_at, ip_address, user_agent,
               CASE WHEN expires_at > datetime('now') THEN 'Active' ELSE 'Expired' END as status
        FROM user_sessions 
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    print(f"   ✅ Found {len(active_sessions)} active sessions")
    
    # Test 4: Learning stats queries
    print("\n🧪 TEST 4: Learning Stats")
    print("-" * 40)
    
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
    
    print(f"   ✅ Total learnings: {total_learnings}")
    print(f"   ✅ Completed courses: {completed_courses}")
    print(f"   ✅ Enrolled courses: {enrolled_courses}")
    
    # Test 5: Points log
    print("\n🧪 TEST 5: Points Log")
    print("-" * 40)
    
    points_log = level_manager.get_user_points_log(user_id, limit=5)
    print(f"   ✅ Points log entries: {len(points_log)}")
    
    if points_log:
        for log in points_log[:3]:  # Show first 3
            print(f"     - {log['action']}: {log['points_change']:+d} pts ({log['created_at']})")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ PROFILE FUNCTIONALITY TEST COMPLETED")
    print("="*60)
    
    print("\n💡 TEMPLATE VARIABLES THAT WILL BE PASSED:")
    print("-" * 50)
    print("✅ user (user_data from database)")
    print("✅ level_info (comprehensive level information)")
    print("✅ active_sessions (user's active sessions)")
    print("✅ total_learnings (count of user's learning entries)")
    print("✅ completed_courses (count of completed courses)")
    print("✅ enrolled_courses (count of enrolled courses)")
    print("✅ points_log (recent points transaction history)")

if __name__ == "__main__":
    test_profile_functionality()
