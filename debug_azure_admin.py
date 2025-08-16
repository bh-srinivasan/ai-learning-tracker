#!/usr/bin/env python3
"""
Debug script to test Azure admin login and identify the exact error.
"""

import requests
import sys

def test_azure_admin_detailed():
    """Test Azure admin login with detailed error reporting."""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("🔍 Azure Admin Login Debug Test")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    
    try:
        # 1. Get login page
        print("1. Getting login page...")
        login_response = session.get(f"{base_url}/login")
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login page failed: {login_response.text[:200]}")
            return False
            
        # 2. Check if we can access admin without login (should redirect)
        print("2. Testing admin access without login...")
        admin_response = session.get(f"{base_url}/admin")
        print(f"   Status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            print("⚠️ Admin accessible without login - security issue!")
        elif admin_response.status_code in [302, 401]:
            print("✅ Admin properly protected")
        
        # 3. Test login with credentials
        print("3. Testing login with admin credentials...")
        password = input("Enter admin password: ").strip()
        
        if not password:
            print("❌ No password provided")
            return False
            
        login_data = {
            'username': 'admin',
            'password': password
        }
        
        login_submit = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        print(f"   Login POST status: {login_submit.status_code}")
        print(f"   Response headers: {dict(login_submit.headers)}")
        
        if login_submit.status_code == 302:
            print("✅ Login succeeded (redirected)")
            redirect_location = login_submit.headers.get('Location', 'No Location header')
            print(f"   Redirect to: {redirect_location}")
        else:
            print(f"❌ Login failed: {login_submit.text[:200]}")
            return False
            
        # 4. Test admin dashboard access after login
        print("4. Testing admin dashboard access after login...")
        admin_dashboard = session.get(f"{base_url}/admin")
        print(f"   Admin dashboard status: {admin_dashboard.status_code}")
        
        if admin_dashboard.status_code == 200:
            print("✅ Admin dashboard accessible")
            # Check for specific content
            if "Admin Dashboard" in admin_dashboard.text:
                print("✅ Admin dashboard content loaded")
            else:
                print("⚠️ Admin dashboard loaded but missing expected content")
        elif admin_dashboard.status_code == 500:
            print("❌ Internal Server Error in admin dashboard")
            print("First 500 chars of error response:")
            print(admin_dashboard.text[:500])
            return False
        else:
            print(f"❌ Unexpected admin dashboard status: {admin_dashboard.status_code}")
            print(f"Response: {admin_dashboard.text[:200]}")
            return False
            
        # 5. Test specific admin functions
        print("5. Testing admin functions...")
        
        # Test users page
        users_response = session.get(f"{base_url}/admin/users")
        print(f"   Users page status: {users_response.status_code}")
        
        if users_response.status_code == 500:
            print("❌ Users page error - admin functions broken")
            return False
        elif users_response.status_code == 200:
            print("✅ Users page accessible")
            
        # Test courses page
        courses_response = session.get(f"{base_url}/admin/courses")
        print(f"   Courses page status: {courses_response.status_code}")
        
        if courses_response.status_code == 500:
            print("❌ Courses page error")
            return False
        elif courses_response.status_code == 200:
            print("✅ Courses page accessible")
            
        print("\n🎉 All admin functions working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_azure_admin_detailed()
    sys.exit(0 if success else 1)
