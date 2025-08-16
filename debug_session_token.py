#!/usr/bin/env python3
"""
Debug session token storage issue
"""

import requests
import json

def debug_session_token():
    """Debug the session token storage issue"""
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("=" * 60)
    print("SESSION TOKEN DEBUG TEST")
    print("=" * 60)
    
    # Step 1: Check initial session state
    print("\n1. Initial Session State:")
    response = session.get(f"{base_url}/debug/session-info")
    if response.status_code == 200:
        data = response.json()
        print(f"   Session Token: {data.get('session_token', 'None')}")
        print(f"   Session Keys: {data.get('session_keys', [])}")
        print(f"   Username: {data.get('username', 'None')}")
    
    # Step 2: Perform login
    print("\n2. Performing Login:")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'  # Correct admin password
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Login Status: {login_response.status_code}")
    print(f"   Redirect: {login_response.headers.get('Location', 'None')}")
    
    # Print any cookies being set
    if 'Set-Cookie' in login_response.headers:
        print(f"   Cookies Set: {login_response.headers['Set-Cookie']}")
    
    # Step 3: Check session after login
    print("\n3. Session State After Login:")
    response = session.get(f"{base_url}/debug/session-info")
    if response.status_code == 200:
        data = response.json()
        print(f"   Session Token: {data.get('session_token', 'None')}")
        print(f"   Session Keys: {data.get('session_keys', [])}")
        print(f"   Username: {data.get('username', 'None')}")
        print(f"   Is Admin: {data.get('is_admin', 'None')}")
        print(f"   User ID: {data.get('user_id', 'None')}")
        print(f"   Session Permanent: {data.get('session_permanent', 'None')}")
    
    # Step 4: Try to access admin dashboard
    print("\n4. Admin Dashboard Access:")
    admin_response = session.get(f"{base_url}/admin")
    print(f"   Status: {admin_response.status_code}")
    
    # Look for specific error messages
    if admin_response.status_code == 200:
        content = admin_response.text.lower()
        if 'please log in to access' in content:
            print("   ❌ Access denied - 'please log in to access' found")
        elif 'admin dashboard' in content or 'admin panel' in content:
            print("   ✅ Access granted - admin content found")
        else:
            print("   ⚠️  Unclear access result")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_session_token()
