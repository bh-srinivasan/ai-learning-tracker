#!/usr/bin/env python3
"""
Auto Admin Initializer
======================

Script to automatically initialize admin user via web route.
"""

import requests
import os

def auto_initialize_admin():
    """Automatically initialize admin user via web route"""
    
    print("=== AUTO ADMIN INITIALIZATION ===")
    
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    init_url = f"{base_url}/initialize-admin"
    
    # Get admin password
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    print(f"🔍 Accessing initialization URL: {init_url}")
    
    try:
        # Create session
        session = requests.Session()
        
        # First get the form
        response = session.get(init_url)
        
        if response.status_code != 200:
            print(f"❌ Failed to access initialization page: {response.status_code}")
            return False
        
        if "Admin User Initialization" in response.text:
            print("✅ Initialization form loaded")
        else:
            print("⚠️ Unexpected page content")
            print(f"Content preview: {response.text[:200]}...")
        
        # Submit the form
        print("🚀 Submitting initialization form...")
        
        form_data = {
            'init_password': admin_password
        }
        
        response = session.post(init_url, data=form_data)
        
        if response.status_code == 200:
            if "Initialization Complete" in response.text:
                print("🎉 ADMIN INITIALIZATION SUCCESSFUL!")
                print("✅ Admin user created via web interface")
                return True
            elif "Admin Already Exists" in response.text:
                print("✅ ADMIN USER ALREADY EXISTS!")
                print("🔧 No action needed - admin is ready")
                return True
            elif "Invalid Password" in response.text:
                print("❌ INVALID INITIALIZATION PASSWORD!")
                print("🔧 Check ADMIN_PASSWORD environment variable")
                return False
            elif "Initialization Failed" in response.text:
                print("❌ INITIALIZATION FAILED!")
                print("Error details in response")
                return False
            else:
                print("⚠️ Unexpected response content")
                print(f"Content preview: {response.text[:300]}...")
                return False
        else:
            print(f"❌ Form submission failed: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return False

def test_admin_login_after_init():
    """Test admin login after initialization"""
    
    print("\n=== TESTING ADMIN LOGIN ===")
    
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    try:
        session = requests.Session()
        
        # Get login page
        response = session.get(base_url)
        if response.status_code != 200:
            print(f"❌ Failed to get login page: {response.status_code}")
            return False
        
        # Submit login
        login_data = {
            'username': 'admin',
            'password': admin_password
        }
        
        response = session.post(base_url, data=login_data, allow_redirects=False)
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/dashboard' in location:
                print("✅ ADMIN LOGIN SUCCESSFUL!")
                print("🎉 Azure deployment is fully working!")
                return True
            else:
                print(f"❌ Login failed - redirected to: {location}")
                return False
        else:
            print(f"❌ Unexpected login response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return False

def main():
    """Main function"""
    
    print("AI Learning Tracker - Auto Admin Initializer")
    print("=" * 60)
    
    # Initialize admin user
    init_success = auto_initialize_admin()
    
    if init_success:
        # Test login
        login_success = test_admin_login_after_init()
        
        print("\n" + "=" * 60)
        print("FINAL SUMMARY:")
        print(f"Admin Initialization: {'✅ SUCCESS' if init_success else '❌ FAILED'}")
        print(f"Admin Login Test:     {'✅ SUCCESS' if login_success else '❌ FAILED'}")
        
        if init_success and login_success:
            print("\n🎉 AZURE DEPLOYMENT IS FULLY OPERATIONAL!")
            print("🔗 URL: https://ai-learning-tracker-bharath.azurewebsites.net/")
            print("👤 Username: admin")
            print("🔑 Password: [from environment variable]")
        else:
            print("\n⚠️ Some issues remain - check logs above")
    else:
        print("\n❌ Initialization failed - cannot proceed with login test")
    
    return init_success

if __name__ == "__main__":
    main()
