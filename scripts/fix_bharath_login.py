#!/usr/bin/env python3
"""
Check bharath user credentials and fix if needed
"""
import sys
sys.path.append('.')

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def check_and_fix_bharath_user():
    """Check bharath user and fix password if needed"""
    print("CHECKING BHARATH USER CREDENTIALS")
    print("=" * 40)
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Check if bharath user exists
    bharath = conn.execute('SELECT * FROM users WHERE username = ?', ('bharath',)).fetchone()
    
    if not bharath:
        print("❌ bharath user not found!")
        return
    
    print(f"✅ Found bharath user (ID: {bharath['id']})")
    print(f"   Username: {bharath['username']}")
    print(f"   Level: {bharath['level']}")
    print(f"   Points: {bharath['points']}")
    print(f"   Password hash: {bharath['password_hash'][:20]}...")
    
    # Test if password 'bharath' works
    if check_password_hash(bharath['password_hash'], 'bharath'):
        print("✅ Password 'bharath' works correctly")
    else:
        print("❌ Password 'bharath' does NOT work")
        print("   Updating password to 'bharath'...")
        
        new_hash = generate_password_hash('bharath')
        conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                    (new_hash, 'bharath'))
        conn.commit()
        
        print("✅ Password updated successfully")
        
        # Verify the update
        bharath_updated = conn.execute('SELECT password_hash FROM users WHERE username = ?', 
                                     ('bharath',)).fetchone()
        
        if check_password_hash(bharath_updated['password_hash'], 'bharath'):
            print("✅ Password verification successful after update")
        else:
            print("❌ Password still doesn't work after update")
    
    conn.close()

def test_bharath_login():
    """Test bharath login after password fix"""
    print("\nTESTING BHARATH LOGIN")
    print("=" * 40)
    
    from app import app
    
    with app.test_client() as client:
        print("Attempting login with bharath/bharath...")
        
        response = client.post('/login', data={
            'username': 'bharath', 
            'password': 'bharath'
        }, follow_redirects=False)
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"Redirected to: {location}")
            
            if 'dashboard' in location or location == '/':
                print("✅ LOGIN SUCCESSFUL!")
                
                # Now test profile access
                profile_response = client.get('/profile')
                print(f"Profile access status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    print("✅ PROFILE PAGE ACCESSIBLE!")
                    
                    content = profile_response.data.decode('utf-8')
                    if 'Internal Server Error' in content:
                        print("❌ Internal Server Error detected in profile page")
                        print("First 500 chars of error:")
                        print(content[:500])
                    elif 'My Profile' in content:
                        print("✅ Profile page loaded successfully")
                        print(f"Content length: {len(content)} characters")
                    else:
                        print("⚠️  Profile page loaded but content seems unusual")
                        print("First 200 chars:")
                        print(content[:200])
                        
                elif profile_response.status_code == 302:
                    print(f"Profile page redirected to: {profile_response.headers.get('Location')}")
                else:
                    print(f"❌ Profile page error: {profile_response.status_code}")
                    
            else:
                print(f"❌ Login failed - redirected to: {location}")
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            print("Response data:")
            print(response.data.decode('utf-8')[:300])

if __name__ == "__main__":
    check_and_fix_bharath_user()
    test_bharath_login()
