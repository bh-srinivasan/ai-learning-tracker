#!/usr/bin/env python3
"""Check memory sessions in Flask app"""

import requests
import time

def test_session_creation():
    print("🔍 Testing session creation and memory storage...")
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # 1. Login first
    print("🔑 Logging in as admin...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Login status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("   ✅ Login successful (redirect)")
        
        # 2. Check session debug endpoint if it exists
        print("🔍 Checking session debug info...")
        try:
            debug_response = session.get(f"{base_url}/debug-session")
            if debug_response.status_code == 200:
                print(f"   Session debug info: {debug_response.text[:200]}...")
            else:
                print(f"   No debug endpoint (status: {debug_response.status_code})")
        except:
            print("   No debug endpoint available")
        
        # 3. Try admin access
        print("🎯 Attempting admin access...")
        admin_response = session.get(f"{base_url}/admin", allow_redirects=False)
        print(f"   Admin access status: {admin_response.status_code}")
        
        if admin_response.status_code == 302:
            redirect_to = admin_response.headers.get('Location', 'Unknown')
            print(f"   🔄 Redirected to: {redirect_to}")
            if '/login' in redirect_to:
                print("   ❌ Session validation failing - redirected to login")
            else:
                print("   ✅ Valid redirect to another admin page")
        elif admin_response.status_code == 200:
            print("   ✅ Admin page loaded successfully")
            if "Database error occurred" in admin_response.text:
                print("   ❌ But database error found in content!")
        
    else:
        print("   ❌ Login failed")

if __name__ == "__main__":
    test_session_creation()
