#!/usr/bin/env python3
"""
Test script to diagnose the profile page Internal Server Error
"""
import sys
sys.path.append('.')

from app import app
import sqlite3
from flask import session

def test_profile_route():
    """Test the profile route to identify the Internal Server Error"""
    print("TESTING PROFILE ROUTE FOR INTERNAL SERVER ERROR")
    print("=" * 60)
    
    # Check if database and users exist
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    print("1. Checking database and users...")
    users = conn.execute('SELECT id, username FROM users WHERE username != "admin"').fetchall()
    
    if not users:
        print("❌ No non-admin users found in database!")
        return
    
    test_user = users[0]
    print(f"✅ Found test user: {test_user['username']} (ID: {test_user['id']})")
    
    # Test profile route with Flask test client
    print("\n2. Testing profile route with Flask test client...")
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Simulate user login by setting session
                with client.session_transaction() as sess:
                    sess['user_id'] = test_user['id']
                    sess['username'] = test_user['username']
                
                print(f"   Simulating request to /profile for user {test_user['username']}")
                
                # Make request to profile page
                response = client.get('/profile')
                
                print(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ SUCCESS: Profile page loaded without error")
                    print(f"   Response length: {len(response.data)} bytes")
                elif response.status_code == 302:
                    print(f"🔄 REDIRECT: {response.headers.get('Location', 'Unknown location')}")
                elif response.status_code == 500:
                    print("❌ INTERNAL SERVER ERROR detected!")
                    print("   Response data:")
                    print(response.data.decode('utf-8')[:500] + "..." if len(response.data) > 500 else response.data.decode('utf-8'))
                else:
                    print(f"❌ UNEXPECTED STATUS: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ EXCEPTION during profile route test: {e}")
                import traceback
                traceback.print_exc()
    
    conn.close()

def test_profile_route_components():
    """Test individual components that the profile route uses"""
    print("\n3. Testing profile route components...")
    print("-" * 40)
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Get a test user
    test_user = conn.execute('SELECT id, username FROM users WHERE username != "admin" LIMIT 1').fetchone()
    
    if not test_user:
        print("❌ No test user available")
        return
    
    user_id = test_user['id']
    print(f"Testing components for user ID: {user_id}")
    
    try:
        # Test LevelManager import and initialization
        print("\n   Testing LevelManager...")
        from level_manager import LevelManager
        level_manager = LevelManager()
        print("   ✅ LevelManager imported and initialized")
        
        # Test get_user_level_info
        print("\n   Testing get_user_level_info...")
        level_info = level_manager.get_user_level_info(user_id)
        if level_info:
            print("   ✅ Level info retrieved successfully")
            print(f"      Current level: {level_info.get('current_level', 'Unknown')}")
        else:
            print("   ❌ Failed to get level info")
        
        # Test user data query
        print("\n   Testing user data query...")
        user_data = conn.execute('''
            SELECT username, level, points, level_points, user_selected_level, created_at, 
                   last_login, last_activity, login_count
            FROM users 
            WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if user_data:
            print("   ✅ User data query successful")
            print(f"      Username: {user_data['username']}")
            print(f"      Level: {user_data['level']}")
            print(f"      Points: {user_data['points']}")
        else:
            print("   ❌ User data query failed")
        
        # Test active sessions query
        print("\n   Testing active sessions query...")
        active_sessions = conn.execute('''
            SELECT session_token, created_at, expires_at, ip_address, user_agent,
                   CASE WHEN expires_at > datetime('now') THEN 'Active' ELSE 'Expired' END as status
            FROM user_sessions 
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
        ''', (user_id,)).fetchall()
        
        print(f"   ✅ Active sessions query successful - found {len(active_sessions)} sessions")
        
        # Test learning stats queries
        print("\n   Testing learning stats queries...")
        
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
        
        print(f"   ✅ Learning stats - Total: {total_learnings}, Completed: {completed_courses}, Enrolled: {enrolled_courses}")
        
        # Test points log
        print("\n   Testing points log...")
        points_log = level_manager.get_user_points_log(user_id, limit=10)
        print(f"   ✅ Points log retrieved - {len(points_log) if points_log else 0} entries")
        
        print("\n✅ ALL PROFILE ROUTE COMPONENTS WORKING")
        
    except Exception as e:
        print(f"\n❌ ERROR in profile route components: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

def test_template_rendering():
    """Test if the profile template can render with sample data"""
    print("\n4. Testing profile template rendering...")
    print("-" * 40)
    
    with app.app_context():
        try:
            from flask import render_template
            
            # Create sample data similar to what the route provides
            sample_user = {
                'username': 'test_user',
                'level': 2,
                'points': 150,
                'level_points': 50,
                'user_selected_level': 'Intermediate',
                'created_at': '2025-01-01 10:00:00',
                'last_login': '2025-01-02 10:00:00',
                'last_activity': '2025-01-02 11:00:00',
                'login_count': 5
            }
            
            sample_level_info = {
                'current_level': 2,
                'current_level_name': 'Beginner',
                'points_needed_for_next': 50,
                'next_level': 3,
                'next_level_name': 'Intermediate',
                'progress_percentage': 50,
                'total_points': 150,
                'level_points': 50
            }
            
            sample_active_sessions = [
                {
                    'session_token': 'test123',
                    'created_at': '2025-01-02 10:00:00',
                    'expires_at': '2025-01-03 10:00:00',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Test Browser',
                    'status': 'Active'
                }
            ]
            
            sample_points_log = [
                {
                    'action_type': 'course_completion',
                    'points_earned': 20,
                    'description': 'Completed Test Course',
                    'created_at': '2025-01-02 10:00:00'
                }
            ]
            
            # Try to render the template
            result = render_template('dashboard/profile.html',
                                   user=sample_user,
                                   level_info=sample_level_info,
                                   active_sessions=sample_active_sessions,
                                   total_learnings=5,
                                   completed_courses=2,
                                   enrolled_courses=3,
                                   points_log=sample_points_log)
            
            print("✅ Profile template rendered successfully")
            print(f"   Template length: {len(result)} characters")
            
        except Exception as e:
            print(f"❌ Template rendering error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_profile_route()
    test_profile_route_components()
    test_template_rendering()
