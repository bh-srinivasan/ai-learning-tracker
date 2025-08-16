#!/usr/bin/env python3
"""Test each admin dashboard database query individually"""

import sqlite3

def test_admin_dashboard_queries():
    print("🔍 Testing admin dashboard database queries...")
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Test 1: User count
    print("👥 Testing user count query...")
    try:
        result = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
        user_count = result[0] if hasattr(result, '__getitem__') else result
        if hasattr(result, 'keys') and 'count' in result:
            user_count = result['count']
        print(f"   ✅ User count: {user_count}")
    except Exception as e:
        print(f"   ❌ User count error: {e}")
    
    # Test 2: Course count
    print("📚 Testing course count query...")
    try:
        result = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()
        course_count = result[0] if hasattr(result, '__getitem__') else result
        if hasattr(result, 'keys') and 'count' in result:
            course_count = result['count']
        print(f"   ✅ Course count: {course_count}")
    except Exception as e:
        print(f"   ❌ Course count error: {e}")
    
    # Test 3: Learning entries count
    print("📖 Testing learning entries count query...")
    try:
        result = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()
        learning_count = result[0] if hasattr(result, '__getitem__') else result
        if hasattr(result, 'keys') and 'count' in result:
            learning_count = result['count']
        print(f"   ✅ Learning count: {learning_count}")
    except Exception as e:
        print(f"   ❌ Learning count error: {e}")
    
    # Test 4: Recent users
    print("🕐 Testing recent users query...")
    try:
        recent_users = conn.execute('''
            SELECT username, level, points, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        ''').fetchall()
        print(f"   ✅ Recent users count: {len(recent_users)}")
        for user in recent_users:
            print(f"      - {user['username']} ({user['level']}) - {user['points']} points")
    except Exception as e:
        print(f"   ❌ Recent users error: {e}")
    
    conn.close()
    print("🎉 All individual queries tested!")

if __name__ == "__main__":
    test_admin_dashboard_queries()
