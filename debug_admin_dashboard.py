#!/usr/bin/env python3
"""
Debug script to test admin dashboard database operations step by step
"""

import sqlite3
import os
from dotenv import load_dotenv

def test_admin_dashboard_queries():
    """Test each database query that the admin dashboard performs"""
    
    # Load environment
    load_dotenv()
    
    print("🔍 Testing admin dashboard database operations...")
    
    try:
        # Test 1: Database connection
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row  # Enable row access like Flask app
        print("✅ Database connection successful")
        
        # Test 2: Check session table exists
        session_table = 'user_sessions'
        try:
            result = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{session_table}'").fetchone()
            if result:
                print(f"✅ Session table '{session_table}' exists")
            else:
                print(f"❌ Session table '{session_table}' does not exist")
                return False
        except Exception as e:
            print(f"❌ Error checking session table: {e}")
            return False
        
        # Test 3: Check admin user exists
        try:
            admin_user = conn.execute('SELECT id, username, level, points FROM users WHERE username = ?', ('admin',)).fetchone()
            if admin_user:
                print(f"✅ Admin user found: ID={admin_user['id']}, Level={admin_user['level']}")
            else:
                print("❌ Admin user not found")
                return False
        except Exception as e:
            print(f"❌ Error checking admin user: {e}")
            return False
        
        # Test 4: Test count queries (like admin dashboard does)
        try:
            result = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
            user_count = result['count'] if result else 0
            print(f"✅ User count query successful: {user_count} users")
        except Exception as e:
            print(f"❌ Error getting user count: {e}")
            return False
        
        try:
            result = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()
            course_count = result['count'] if result else 0
            print(f"✅ Course count query successful: {course_count} courses")
        except Exception as e:
            print(f"❌ Error getting course count: {e}")
            return False
        
        try:
            result = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()
            learning_count = result['count'] if result else 0
            print(f"✅ Learning entries count query successful: {learning_count} entries")
        except Exception as e:
            print(f"❌ Error getting learning count: {e}")
            return False
        
        # Test 5: Test recent users query
        try:
            recent_users = conn.execute('''
                SELECT username, level, points, created_at 
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 5
            ''').fetchall()
            print(f"✅ Recent users query successful: {len(recent_users)} users found")
            for user in recent_users:
                print(f"   - {user['username']} ({user['level']}) - {user['points']} points")
        except Exception as e:
            print(f"❌ Error getting recent users: {e}")
            return False
        
        # Test 6: Test session lookup query (simulate what happens during login)
        try:
            # Get a recent session token for testing
            recent_session = conn.execute('SELECT session_token FROM user_sessions WHERE user_id = 1 ORDER BY id DESC LIMIT 1').fetchone()
            if recent_session:
                session_token = recent_session['session_token']
                print(f"✅ Found test session token: {session_token[:10]}...")
                
                # Test the join query that admin dashboard uses
                user_session = conn.execute(f'''
                    SELECT s.user_id, u.username, u.level, u.points 
                    FROM {session_table} s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE s.session_token = ? AND s.is_active = ?
                ''', (session_token, 1)).fetchone()
                
                if user_session:
                    print(f"✅ Session join query successful: User {user_session['username']}")
                else:
                    print("⚠️ Session join query returned no results (session might be inactive)")
            else:
                print("⚠️ No sessions found for testing")
        except Exception as e:
            print(f"❌ Error testing session lookup: {e}")
            return False
        
        conn.close()
        print("\n🎉 All admin dashboard database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Critical error in database tests: {e}")
        return False

def test_template_exists():
    """Test if admin template exists"""
    template_path = 'templates/admin/index.html'
    if os.path.exists(template_path):
        print(f"✅ Admin template exists: {template_path}")
        return True
    else:
        print(f"❌ Admin template missing: {template_path}")
        return False

def main():
    """Main test function"""
    print("🚀 Debugging admin dashboard database errors...")
    
    db_success = test_admin_dashboard_queries()
    template_success = test_template_exists()
    
    if db_success and template_success:
        print("\n✅ ALL TESTS PASSED - Database operations should work")
        print("The error might be in session management or template rendering.")
    else:
        print("\n❌ TESTS FAILED - Found database issues")
        print("Please fix the identified issues before testing admin login.")

if __name__ == "__main__":
    main()
