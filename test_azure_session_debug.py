#!/usr/bin/env python3
"""
Test Azure session debugging by examining session state
"""
import requests
import os

def test_azure_session_debug():
    """Test Azure session management with detailed analysis"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("🔍 Azure Session Debug Test")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    
    # 1. Test accessing admin without login
    print("1. Testing admin access without login...")
    admin_no_auth = session.get(f"{base_url}/admin")
    print(f"   Status: {admin_no_auth.status_code}")
    
    if admin_no_auth.status_code == 200:
        print("   ❌ Admin page accessible without login!")
        if "Admin Dashboard" in admin_no_auth.text:
            print("   ❌ Admin dashboard content visible without authentication")
        else:
            print("   🔍 No admin content - likely redirected to login form")
    
    # 2. Check for session cookie
    print("2. Checking session cookies...")
    print(f"   Cookies after admin access: {session.cookies}")
    
    # 3. Login with credentials
    print("3. Performing login...")
    password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    
    login_data = {
        'username': 'admin',
        'password': password
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Login status: {login_response.status_code}")
    print(f"   Login cookies: {session.cookies}")
    
    # Look for session token in cookies
    session_token = None
    for cookie in session.cookies:
        if cookie.name == 'session':
            session_token = cookie.value
            print(f"   Session token found: {session_token[:50]}...")
            break
    
    if not session_token:
        print("   ❌ No session token in cookies!")
        return False
    
    # 4. Test admin access after login
    print("4. Testing admin access after login...")
    admin_after_login = session.get(f"{base_url}/admin")
    print(f"   Admin status: {admin_after_login.status_code}")
    
    if admin_after_login.status_code == 500:
        print("   ❌ Internal Server Error - checking response...")
        # Try to get debug info endpoint
        debug_response = session.get(f"{base_url}/debug-session")
        if debug_response.status_code == 200:
            print(f"   Debug info: {debug_response.text}")
    
    # 5. Test a simple authenticated page
    print("5. Testing dashboard access...")
    dashboard_response = session.get(f"{base_url}/dashboard")
    print(f"   Dashboard status: {dashboard_response.status_code}")
    
    if dashboard_response.status_code == 200:
        print("   ✅ Dashboard accessible - session working for regular pages")
    elif dashboard_response.status_code == 302:
        print("   🔄 Dashboard redirected - might be unauthenticated")
    
    return admin_after_login.status_code == 200

if __name__ == "__main__":
    success = test_azure_session_debug()
    if success:
        print("\n✅ Admin access working!")
    else:
        print("\n❌ Admin access still failing")
