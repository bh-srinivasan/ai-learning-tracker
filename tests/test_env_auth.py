#!/usr/bin/env python3
"""
Secure test script that uses environment variables for passwords
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_secure_login():
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # Get passwords from environment
    admin_password = os.environ.get('ADMIN_PASSWORD')
    demo_password = os.environ.get('DEMO_PASSWORD')
    
    if not admin_password:
        print("❌ ADMIN_PASSWORD not found in environment variables")
        return False
        
    print("🔐 Testing with environment variable passwords...")
    print(f"   Admin password length: {len(admin_password)} characters")
    print(f"   Demo password length: {len(demo_password) if demo_password else 0} characters")
    
    # Test admin login
    print("\n--- Testing Admin Login (Environment Variable) ---")
    login_url = f"{base_url}/login"
    login_data = {
        'username': 'admin',
        'password': admin_password
    }
    
    response = session.post(login_url, data=login_data, allow_redirects=False)
    print(f"Admin login response: {response.status_code}")
    print(f"Location header: {response.headers.get('Location', 'None')}")
    
    if response.status_code in [302, 303]:
        # Follow redirect
        redirect_url = response.headers.get('Location')
        if redirect_url:
            if redirect_url.startswith('/'):
                redirect_url = base_url + redirect_url
            redirect_response = session.get(redirect_url)
            print(f"✅ Admin login successful - Status: {redirect_response.status_code}")
            return True
    else:
        print(f"❌ Admin login failed - Status: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_secure_login()
    if success:
        print("\n🎉 Environment variable authentication working correctly!")
    else:
        print("\n⚠️ Environment variable authentication needs attention")
