#!/usr/bin/env python3
"""
Direct database verification via admin interface
"""
import requests
import time

# Azure application URL
AZURE_URL = "https://ai-learning-tracker-bharath.azurewebsites.net"

def check_admin_access():
    """Try to access admin interface to verify users"""
    print("🔧 Checking admin interface access...")
    
    try:
        # Try admin login
        session = requests.Session()
        admin_login_data = {
            'username': 'admin',
            'password': 'admin'
        }
        
        print("🔐 Attempting admin login...")
        login_response = session.post(f"{AZURE_URL}/login", data=admin_login_data, timeout=30, allow_redirects=True)
        
        print(f"Admin login response status: {login_response.status_code}")
        print(f"Admin login final URL: {login_response.url}")
        
        if "dashboard" in login_response.url or login_response.status_code == 200:
            # Try to access admin users page
            users_response = session.get(f"{AZURE_URL}/admin/users", timeout=30)
            print(f"Admin users page status: {users_response.status_code}")
            
            if users_response.status_code == 200:
                print("✅ Successfully accessed admin users page!")
                # Check if bharath user exists in the response
                if "bharath" in users_response.text:
                    print("✅ User 'bharath' found in admin users list!")
                    return True
                else:
                    print("❌ User 'bharath' NOT found in admin users list!")
                    return False
            else:
                print(f"❌ Failed to access admin users page: {users_response.status_code}")
                return False
        else:
            print("❌ Admin login failed")
            return False
            
    except Exception as e:
        print(f"❌ Error checking admin access: {e}")
        return False

def test_different_credentials():
    """Test with different known credentials"""
    print("🔄 Testing different credential combinations...")
    
    test_accounts = [
        ('admin', 'admin'),
        ('bharath', 'bharath'),  
        ('demo', 'demo'),
        ('test', 'test')
    ]
    
    for username, password in test_accounts:
        try:
            session = requests.Session()
            login_data = {
                'username': username,
                'password': password
            }
            
            print(f"🔐 Testing {username}/{password}...")
            response = session.post(f"{AZURE_URL}/login", data=login_data, timeout=15, allow_redirects=True)
            
            if "dashboard" in response.url:
                print(f"✅ SUCCESS: {username} can login!")
                return True
            elif response.status_code == 200 and "login" not in response.url:
                print(f"✅ SUCCESS: {username} logged in (status 200)")
                return True
            else:
                print(f"❌ Failed: {username} (final URL: {response.url})")
                
        except Exception as e:
            print(f"❌ Error testing {username}: {e}")
    
    return False

def main():
    print("=" * 60)
    print("🔍 USER VERIFICATION AFTER RESTART")
    print("=" * 60)
    
    print("Step 1: Testing different login credentials...")
    login_success = test_different_credentials()
    
    print("\nStep 2: Checking admin interface...")
    admin_success = check_admin_access()
    
    print("\n" + "=" * 60)
    if login_success or admin_success:
        print("✅ VERIFICATION: User data is accessible after restart!")
    else:
        print("❌ VERIFICATION: Issues with user access after restart")
    print("=" * 60)

if __name__ == "__main__":
    main()
