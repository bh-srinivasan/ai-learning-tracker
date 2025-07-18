#!/usr/bin/env python3
"""
Web-based Admin Initializer
============================

Simple web request to trigger admin user creation on Azure.
"""

import requests
import os

def trigger_admin_init():
    """Trigger admin initialization via web request"""
    
    print("=== WEB-BASED ADMIN INITIALIZATION ===")
    
    # We'll make a special request to trigger initialization
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    # Create a session
    session = requests.Session()
    
    try:
        # First check if app is responding
        print("🔍 Checking app status...")
        response = session.get(base_url)
        
        if response.status_code == 200:
            print("✅ Azure app is responding")
        else:
            print(f"❌ App not responding: {response.status_code}")
            return False
        
        # Since we can't directly execute the script via web request,
        # let's check if we can determine the database state
        print("🔍 Testing login to determine database state...")
        
        # Try login with admin credentials
        login_data = {
            'username': 'admin',
            'password': os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
        }
        
        response = session.post(base_url, data=login_data, allow_redirects=False)
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/dashboard' in location:
                print("✅ Admin user already exists and works!")
                return True
            else:
                print("❌ Admin login failed - user likely doesn't exist in Azure DB")
                return False
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    success = trigger_admin_init()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ADMIN USER IS READY!")
        print("✅ You can login to your Azure app")
    else:
        print("❌ ADMIN USER NEEDS TO BE CREATED")
        print("💡 The Azure database is likely empty")
        print("🔧 Need to run initialization script on Azure")
    
    return success

if __name__ == "__main__":
    main()
