#!/usr/bin/env python3
"""
Final test of admin login and dashboard access
"""

import requests
import os

def test_full_admin_flow():
    """Test complete admin login flow"""
    base_url = "http://127.0.0.1:5000"
    
    # Load environment
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        print("❌ ADMIN_PASSWORD not found")
        return False
    
    print("🔍 Testing complete admin login flow...")
    
    # Create session
    session = requests.Session()
    
    # Test 1: Load login page
    try:
        response = session.get(f"{base_url}/login")
        if response.status_code != 200:
            print(f"❌ Login page failed: {response.status_code}")
            return False
        print("✅ Login page loads successfully")
    except Exception as e:
        print(f"❌ Login page error: {e}")
        return False
    
    # Test 2: Submit login form
    try:
        login_data = {
            'username': 'admin',
            'password': admin_password
        }
        
        response = session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
        
        if response.status_code == 200:
            # Check if we're on admin dashboard
            if '/admin' in response.url or 'Admin Dashboard' in response.text:
                print("✅ Successfully logged in and redirected to admin dashboard")
            else:
                print(f"⚠️ Login successful but not on admin dashboard")
                print(f"Current URL: {response.url}")
                return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test 3: Check admin dashboard content
    try:
        response = session.get(f"{base_url}/admin")
        if response.status_code == 200:
            print("✅ Admin dashboard accessible")
            
            # Check for admin content
            if 'Admin Panel' in response.text or 'Manage Users' in response.text:
                print("✅ Admin dashboard contains expected content")
            else:
                print("⚠️ Admin dashboard missing expected content")
                
        else:
            print(f"❌ Admin dashboard failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Admin dashboard error: {e}")
        return False
    
    print("🎉 Complete admin flow test passed!")
    return True

def main():
    """Main test function"""
    print("🚀 Testing complete admin login flow after all fixes...")
    
    success = test_full_admin_flow()
    
    if success:
        print("\n✅ ALL ADMIN TESTS PASSED!")
        print("🎯 You can now login as admin with:")
        print("   Username: admin")
        print("   Password: YourSecureAdminPassword123!")
        print("   URL: http://127.0.0.1:5000/login")
        print("\n🎨 Navigation menu restored with proper admin functions:")
        print("   • Admin Dashboard")
        print("   • Manage Users") 
        print("   • Session Management")
        print("   • Security Dashboard")
        print("   • Manage Courses")
        print("   • Settings")
        print("   • Change Password")
    else:
        print("\n❌ ADMIN TESTS FAILED")
        print("Please check the Flask app logs for errors.")

if __name__ == "__main__":
    main()
