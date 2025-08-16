#!/usr/bin/env python3
"""Create a test admin route to isolate the issue"""

import requests

def test_with_browser():
    """Test admin access by actually opening a browser session"""
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("🔍 Testing complete admin flow...")
    
    # Step 1: Login
    print("🔑 Step 1: Login...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    print(f"   Login status: {login_response.status_code}")
    print(f"   Login final URL: {login_response.url}")
    
    # Step 2: Check what we have in session by visiting a working page
    print("🏠 Step 2: Test dashboard access...")
    dashboard_response = session.get(f"{base_url}/dashboard")
    print(f"   Dashboard status: {dashboard_response.status_code}")
    print(f"   Dashboard URL: {dashboard_response.url}")
    
    if "Welcome" in dashboard_response.text:
        print("   ✅ Regular dashboard works - session is valid")
    elif dashboard_response.url.endswith('/login'):
        print("   ❌ Regular dashboard also redirects to login - session broken")
        return
    
    # Step 3: Now try admin
    print("👑 Step 3: Test admin access...")
    admin_response = session.get(f"{base_url}/admin")
    print(f"   Admin status: {admin_response.status_code}")
    print(f"   Admin URL: {admin_response.url}")
    
    if admin_response.url.endswith('/login'):
        print("   ❌ Admin redirects to login - admin-specific issue")
        
        # Check for flash messages
        if "Admin privileges required" in admin_response.text:
            print("   💡 Flash message: Admin privileges required")
        elif "Session expired" in admin_response.text:
            print("   💡 Flash message: Session expired")
        elif "Database connection error" in admin_response.text:
            print("   💡 Flash message: Database connection error")
        else:
            print("   💡 No specific flash message found")
    else:
        print("   ✅ Admin access successful!")
        
        if "Database error occurred" in admin_response.text:
            print("   ❌ But database error in content")
        else:
            print("   ✅ Admin page loaded successfully!")

if __name__ == "__main__":
    test_with_browser()
