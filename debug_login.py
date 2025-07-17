#!/usr/bin/env python3
"""
Detailed login debugging
"""
import sys
sys.path.append('.')

import sqlite3
from werkzeug.security import check_password_hash
from app import app

def debug_login_process():
    """Debug the login process step by step"""
    print("DEBUGGING LOGIN PROCESS")
    print("=" * 40)
    
    # Check bharath user in database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    bharath = conn.execute('SELECT * FROM users WHERE username = ?', ('bharath',)).fetchone()
    
    if not bharath:
        print("❌ bharath user not found")
        return
    
    print(f"✅ bharath user found (ID: {bharath['id']})")
    
    # Test password verification
    if check_password_hash(bharath['password_hash'], 'bharath'):
        print("✅ Password verification works")
    else:
        print("❌ Password verification fails")
        return
    
    # Test login with debugging
    with app.test_client() as client:
        print("\nTesting login request...")
        
        # Enable debug mode to see errors
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        
        response = client.post('/login', data={
            'username': 'bharath',
            'password': 'bharath'
        }, follow_redirects=False)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"Redirect location: {location}")
        elif response.status_code == 200:
            content = response.data.decode('utf-8')
            print("Login returned 200, checking for errors...")
            
            if 'Too many failed attempts' in content:
                print("❌ Rate limiting issue")
            elif 'Invalid username or password' in content:
                print("❌ Authentication failed")
            else:
                print("⚠️  Login page returned, unknown reason")
        
        # Check session state
        with client.session_transaction() as sess:
            print(f"Session contents: {dict(sess)}")
    
    conn.close()

def test_minimal_profile_access():
    """Test profile access with manual session setting"""
    print("\nTESTING PROFILE WITH MANUAL SESSION")
    print("=" * 40)
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    bharath = conn.execute('SELECT * FROM users WHERE username = ?', ('bharath',)).fetchone()
    conn.close()
    
    if not bharath:
        print("❌ bharath user not found")
        return
    
    # Create a session manually for testing
    from app import create_user_session
    
    try:
        session_token = create_user_session(bharath['id'], '127.0.0.1', 'Test Client')
        print(f"✅ Created session token: {session_token[:20]}...")
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['session_token'] = session_token
                sess['user_id'] = bharath['id']
                sess['username'] = bharath['username']
            
            print("Testing profile access with manual session...")
            response = client.get('/profile')
            
            print(f"Profile response status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.data.decode('utf-8')
                
                if 'Internal Server Error' in content:
                    print("❌ Internal Server Error in profile page")
                    
                    # Look for specific error indicators
                    if 'Traceback' in content:
                        print("Python traceback found in response")
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'Traceback' in line:
                                print("Error details:")
                                for j in range(i, min(i+10, len(lines))):
                                    print(f"  {lines[j]}")
                                break
                
                elif 'My Profile' in content:
                    print("✅ Profile page loaded successfully!")
                    print(f"Content length: {len(content)} characters")
                    
                    # Check for specific profile sections
                    sections = ['User Information', 'Learning Stats', 'Level Progress']
                    for section in sections:
                        if section in content:
                            print(f"   ✅ Found section: {section}")
                
                else:
                    print("⚠️  Profile page returned unexpected content")
                    print("First 300 characters:")
                    print(content[:300])
                    
            elif response.status_code == 302:
                print(f"Profile redirected to: {response.headers.get('Location')}")
            else:
                print(f"❌ Profile error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error in manual session test: {e}")
        import traceback
        traceback.print_exc()

def check_rate_limiting():
    """Check if rate limiting is blocking the login"""
    print("\nCHECKING RATE LIMITING")
    print("=" * 30)
    
    from app import check_rate_limit, get_attempt_count
    
    client_ip = '127.0.0.1'
    
    # Check current attempt count
    attempts = get_attempt_count(client_ip)
    print(f"Current attempts for {client_ip}: {attempts}")
    
    # Check if rate limit allows requests
    allowed = check_rate_limit(client_ip)
    print(f"Rate limit allows requests: {allowed}")
    
    if not allowed:
        print("❌ Rate limiting is blocking login attempts")
        print("Clearing rate limit for testing...")
        
        # Clear rate limit for testing
        conn = sqlite3.connect('ai_learning.db')
        conn.execute('DELETE FROM rate_limit_attempts WHERE ip_address = ?', (client_ip,))
        conn.commit()
        conn.close()
        
        print("✅ Rate limit cleared")

if __name__ == "__main__":
    check_rate_limiting()
    debug_login_process()
    test_minimal_profile_access()
