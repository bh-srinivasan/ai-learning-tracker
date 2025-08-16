#!/usr/bin/env python3
"""
Test admin login functionality after fixing template issues
"""

import requests
import os

def test_admin_login():
    """Test admin login process"""
    base_url = "http://127.0.0.1:5000"
    
    # Get admin password from environment
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        print("❌ ADMIN_PASSWORD not set in environment")
        return False
    
    print(f"🔍 Testing admin login process...")
    print(f"Admin password from env: {admin_password[:5]}***")
    
    # Test 1: Check if login page loads
    try:
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200:
            print("✅ Login page loads successfully")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login page error: {e}")
        return False
    
    # Test 2: Test admin login endpoint
    try:
        response = requests.get(f"{base_url}/test-admin-login-direct")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Admin login test passed")
                print(f"  - Admin user ID: {result.get('admin_user_id')}")
                print(f"  - Session table: {result.get('session_table_used')}")
                print(f"  - User level: {result.get('user_level')}")
                print(f"  - Backend: {'Azure SQL' if result.get('is_azure_sql') else 'SQLite'}")
            else:
                print(f"❌ Admin login test failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Admin login test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Admin login test error: {e}")
        return False
    
    # Test 3: Test actual login POST
    try:
        session = requests.Session()
        
        # Get CSRF token if needed
        login_response = session.get(f"{base_url}/login")
        
        # Attempt login
        login_data = {
            'username': 'admin',
            'password': admin_password
        }
        
        post_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        
        if post_response.status_code in [302, 303]:  # Redirect means successful login
            print("✅ Admin login POST successful (redirect detected)")
            redirect_location = post_response.headers.get('Location', '')
            print(f"  - Redirect to: {redirect_location}")
        else:
            print(f"❌ Admin login POST failed: {post_response.status_code}")
            print(f"Response: {post_response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Admin login POST error: {e}")
        return False
    
    print("🎉 All admin login tests passed!")
    return True

def main():
    """Main test function"""
    print("🚀 Starting admin login test after template fixes...")
    
    # Load environment variables
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded")
        except ImportError:
            print("⚠️ python-dotenv not available")
    
    success = test_admin_login()
    
    if success:
        print("\n✅ ADMIN LOGIN TEST COMPLETE - ALL TESTS PASSED")
        print("The template routing issues have been fixed!")
    else:
        print("\n❌ ADMIN LOGIN TEST FAILED")
        print("There may still be issues to resolve.")

if __name__ == "__main__":
    main()
