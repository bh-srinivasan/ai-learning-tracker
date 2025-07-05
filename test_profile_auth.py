#!/usr/bin/env python3
"""
Test profile page with proper authentication simulation
"""
import sys
sys.path.append('.')

from app import app
import sqlite3
from werkzeug.test import Client
import json

def test_profile_with_real_authentication():
    """Test profile page by actually logging in first"""
    print("TESTING PROFILE PAGE WITH REAL AUTHENTICATION")
    print("=" * 60)
    
    # Check if we have test users
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    users = conn.execute('SELECT username FROM users WHERE username != "admin"').fetchall()
    if not users:
        print("❌ No test users found. Creating one...")
        
        # Create a test user
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('test123')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, level_points)
            VALUES (?, ?, ?, ?, ?)
        ''', ('testuser', password_hash, 'Beginner', 0, 0))
        conn.commit()
        print("✅ Created test user: testuser / test123")
    else:
        print(f"✅ Found test users: {[u['username'] for u in users]}")
    
    conn.close()
    
    # Test the actual login flow and profile access
    with app.test_client() as client:
        print("\n1. Testing login...")
        
        # Try to login with bharath/bharath (known test user)
        login_response = client.post('/login', data={
            'username': 'bharath',
            'password': 'bharath'
        }, follow_redirects=False)
        
        print(f"   Login response status: {login_response.status_code}")
        
        if login_response.status_code == 302:
            redirect_location = login_response.headers.get('Location', '')
            print(f"   Login redirected to: {redirect_location}")
            
            if 'dashboard' in redirect_location or redirect_location.endswith('/'):
                print("   ✅ Login successful")
                
                print("\n2. Testing profile page access...")
                
                # Now try to access profile page
                profile_response = client.get('/profile', follow_redirects=True)
                
                print(f"   Profile response status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    print("   ✅ SUCCESS: Profile page loaded successfully!")
                    
                    # Check if the content looks right
                    content = profile_response.data.decode('utf-8')
                    
                    if 'My Profile' in content:
                        print("   ✅ Profile page contains expected title")
                    
                    if 'bharath' in content.lower():
                        print("   ✅ Profile page shows user information")
                    
                    # Check for specific profile elements
                    profile_indicators = [
                        'level', 'points', 'Learning Stats', 
                        'Recent Activity', 'Session Management'
                    ]
                    
                    found_indicators = []
                    for indicator in profile_indicators:
                        if indicator.lower() in content.lower():
                            found_indicators.append(indicator)
                    
                    print(f"   ✅ Found profile elements: {found_indicators}")
                    
                    # Check content length
                    print(f"   📊 Profile page size: {len(content)} characters")
                    
                elif profile_response.status_code == 302:
                    print(f"   🔄 Profile page redirected to: {profile_response.headers.get('Location', 'Unknown')}")
                else:
                    print(f"   ❌ Profile page error: {profile_response.status_code}")
                    
                    # If there's an error, show some of the content
                    if hasattr(profile_response, 'data'):
                        error_content = profile_response.data.decode('utf-8')[:500]
                        print(f"   Error content preview: {error_content}")
            else:
                print(f"   ❌ Login failed - redirected to: {redirect_location}")
        else:
            print(f"   ❌ Login request failed with status: {login_response.status_code}")

def test_profile_error_scenarios():
    """Test potential error scenarios that could cause Internal Server Error"""
    print("\n3. Testing potential error scenarios...")
    print("-" * 40)
    
    with app.test_client() as client:
        print("   Testing profile access without login...")
        
        # Try to access profile without being logged in
        response = client.get('/profile')
        
        if response.status_code == 302:
            print("   ✅ Correctly redirected to login when not authenticated")
        else:
            print(f"   ❌ Unexpected response when not logged in: {response.status_code}")
        
        # Test with invalid session
        print("   Testing profile with invalid session...")
        
        with client.session_transaction() as sess:
            sess['session_token'] = 'invalid_token_123'
        
        response = client.get('/profile')
        
        if response.status_code == 302:
            print("   ✅ Correctly handled invalid session")
        else:
            print(f"   ❌ Unexpected response with invalid session: {response.status_code}")

def check_database_integrity():
    """Check if database has required tables and columns for profile page"""
    print("\n4. Checking database integrity for profile page...")
    print("-" * 40)
    
    conn = sqlite3.connect('ai_learning.db')
    
    try:
        # Check if all required tables exist
        tables = conn.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('users', 'user_sessions', 'learning_entries', 'user_courses', 'points_log')
        ''').fetchall()
        
        table_names = [t[0] for t in tables]
        
        required_tables = ['users', 'user_sessions', 'learning_entries', 'user_courses']
        missing_tables = [t for t in required_tables if t not in table_names]
        
        if missing_tables:
            print(f"   ❌ Missing required tables: {missing_tables}")
        else:
            print("   ✅ All required tables exist")
        
        # Check users table columns
        print("   Checking users table structure...")
        users_columns = conn.execute('PRAGMA table_info(users)').fetchall()
        users_column_names = [col[1] for col in users_columns]
        
        required_user_columns = [
            'id', 'username', 'level', 'points', 'level_points', 
            'user_selected_level', 'created_at', 'last_login', 'last_activity'
        ]
        
        missing_user_columns = [col for col in required_user_columns if col not in users_column_names]
        
        if missing_user_columns:
            print(f"   ❌ Missing user columns: {missing_user_columns}")
        else:
            print("   ✅ Users table has all required columns")
            
        # Check if there are actual users
        user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        print(f"   📊 Total users in database: {user_count}")
        
    except Exception as e:
        print(f"   ❌ Database integrity check error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_integrity()
    test_profile_with_real_authentication() 
    test_profile_error_scenarios()
