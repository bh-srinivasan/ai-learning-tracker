#!/usr/bin/env python3
"""
Test the admin-test route to find the specific error
"""
import requests

def test_admin_debug():
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    session = requests.Session()
    
    print("🔧 Testing Admin Debug Route")
    print("=" * 40)
    
    # Login first
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    if login_response.status_code != 302:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    print("✅ Login successful")
    
    # Test the admin-test route
    test_response = session.get(f"{base_url}/admin-test")
    print(f"Admin-test status: {test_response.status_code}")
    print(f"Response: {test_response.text}")

if __name__ == "__main__":
    test_admin_debug()
