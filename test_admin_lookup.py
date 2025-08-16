#!/usr/bin/env python3
"""Test the exact admin dashboard database lookup"""

import sqlite3
import secrets

def test_admin_dashboard_lookup():
    print("🔍 Testing admin dashboard database lookup...")
    
    # Get the most recent session for admin user
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find admin user's most recent active session
    print("📋 Finding admin user's active session...")
    cursor.execute("""
        SELECT s.session_token, s.user_id, s.is_active, u.username 
        FROM user_sessions s 
        JOIN users u ON s.user_id = u.id 
        WHERE u.username = 'admin' AND s.is_active = 1
        ORDER BY s.created_at DESC 
        LIMIT 1
    """)
    
    active_session = cursor.fetchone()
    if active_session:
        print(f"✅ Found active admin session: {active_session['session_token'][:10]}...")
        session_token = active_session['session_token']
        
        # Test the exact query used in admin_dashboard
        print("🔍 Testing admin dashboard lookup query...")
        cursor.execute("""
            SELECT s.user_id, u.username, u.level, u.points 
            FROM user_sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = ?
        """, (session_token, True))
        
        user_session = cursor.fetchone()
        if user_session:
            print("✅ Admin dashboard query successful!")
            print(f"   User ID: {user_session['user_id']}")
            print(f"   Username: {user_session['username']}")
            print(f"   Level: {user_session['level']}")
            print(f"   Points: {user_session['points']}")
            
            # Test the specific condition that might be failing
            user_data = {
                'id': user_session['user_id'],
                'username': user_session['username'],
                'level': user_session['level'],
                'points': user_session['points']
            }
            
            admin_check = user_data.get('username') == 'admin'
            print(f"✅ Admin check result: {admin_check}")
            
            if not admin_check:
                print(f"❌ Admin check failed! Username: '{user_data.get('username')}'")
            else:
                print("🎉 All admin dashboard checks should pass!")
                
        else:
            print("❌ Admin dashboard query failed - no results")
            
        # Test with different boolean values
        print("\n🔍 Testing different boolean values for is_active...")
        for test_value in [True, 1, '1', 'true']:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM user_sessions s 
                WHERE s.session_token = ? AND s.is_active = ?
            """, (session_token, test_value))
            result = cursor.fetchone()
            print(f"   is_active = {test_value} ({type(test_value).__name__}): {result['count']} results")
            
    else:
        print("❌ No active admin session found!")
        
        # Check if admin has any sessions at all
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM user_sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE u.username = 'admin'
        """)
        result = cursor.fetchone()
        print(f"   Admin has {result['count']} total sessions")
    
    conn.close()

if __name__ == "__main__":
    test_admin_dashboard_lookup()
