#!/usr/bin/env python3
"""
Simple profile test by accessing it directly through the Flask app
"""
import sys
sys.path.append('.')

from app import app
import sqlite3

def simple_profile_test():
    """Test profile page by using Flask test client properly"""
    print("SIMPLE PROFILE TEST")
    print("=" * 30)
    
    # Test the live Flask app
    print("Starting Flask test...")
    
    with app.test_client() as client:
        # First, check if we can reach the login page
        print("1. Testing login page access...")
        login_response = client.get('/login')
        print(f"   Login page status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print("❌ Cannot access login page")
            return
        
        # Create a proper user session manually by accessing the database
        print("2. Creating manual session...")
        
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        # Get bharath user
        bharath = conn.execute('SELECT * FROM users WHERE username = ?', ('bharath',)).fetchone()
        
        if not bharath:
            print("❌ bharath user not found")
            conn.close()
            return
        
        print(f"   Found user: {bharath['username']} (ID: {bharath['id']})")
        
        # Check if there are any existing sessions for this user
        existing_sessions = conn.execute('''
            SELECT session_token FROM user_sessions 
            WHERE user_id = ? AND is_active = 1 AND expires_at > datetime('now')
            LIMIT 1
        ''', (bharath['id'],)).fetchone()
        
        if existing_sessions:
            session_token = existing_sessions['session_token']
            print(f"   Using existing session: {session_token[:20]}...")
        else:
            # Create a new session
            import secrets
            from datetime import datetime, timedelta
            
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            conn.execute('''
                INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (bharath['id'], session_token, '127.0.0.1', 'Test Client', expires_at, 1))
            conn.commit()
            
            print(f"   Created new session: {session_token[:20]}...")
        
        conn.close()
        
        # Set the session in the test client
        with client.session_transaction() as sess:
            sess['session_token'] = session_token
            sess['user_id'] = bharath['id']
            sess['username'] = bharath['username']
        
        print("3. Testing profile page access...")
        
        try:
            response = client.get('/profile')
            print(f"   Profile response status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.data.decode('utf-8')
                print("   ✅ Profile page loaded successfully!")
                
                # Check for key profile elements
                checks = [
                    ('My Profile', 'Profile title'),
                    ('bharath', 'Username'),
                    ('Level', 'Level information'),
                    ('Points', 'Points information'),
                    ('Learning Stats', 'Learning statistics')
                ]
                
                for check_text, description in checks:
                    if check_text in content:
                        print(f"   ✅ Found: {description}")
                    else:
                        print(f"   ⚠️  Missing: {description}")
                
                print(f"   📊 Content length: {len(content)} characters")
                
                # Check specifically for error indicators
                error_indicators = ['Internal Server Error', 'Traceback', 'Error 500', 'Exception']
                
                for indicator in error_indicators:
                    if indicator in content:
                        print(f"   ❌ ERROR FOUND: {indicator}")
                        
                        # Extract error details
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if indicator in line:
                                print("   Error context:")
                                start = max(0, i-2)
                                end = min(len(lines), i+5)
                                for j in range(start, end):
                                    print(f"     {j}: {lines[j][:100]}")
                                break
                        return
                
                print("   ✅ No error indicators found - Profile page appears healthy!")
                
            elif response.status_code == 302:
                redirect_url = response.headers.get('Location', 'Unknown')
                print(f"   🔄 Profile page redirected to: {redirect_url}")
                
                if 'login' in redirect_url.lower():
                    print("   ❌ Authentication failed - redirected to login")
                else:
                    print("   ⚠️  Unexpected redirect")
                    
            elif response.status_code == 500:
                print("   ❌ INTERNAL SERVER ERROR confirmed!")
                content = response.data.decode('utf-8')
                print("   Error details (first 1000 chars):")
                print(content[:1000])
                
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception during profile test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    simple_profile_test()
