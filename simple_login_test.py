#!/usr/bin/env python3
"""Simple login test to isolate the issue"""

import requests

def simple_login_test():
    print("🔍 Simple login test...")
    
    base_url = "http://localhost:5000"
    
    # Create a session
    session = requests.Session()
    
    # Test 1: Get login page
    print("📝 Getting login page...")
    login_page = session.get(f"{base_url}/login")
    print(f"   Status: {login_page.status_code}")
    
    # Test 2: Submit login
    print("🔑 Submitting login...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    # Submit login WITHOUT following redirects to see exact response
    login_response = session.post(
        f"{base_url}/login",
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   Status: {login_response.status_code}")
    print(f"   Headers: {dict(login_response.headers)}")
    
    # Check for flash messages in response
    if login_response.status_code == 200:
        # Login failed, stayed on login page
        if "Invalid username or password" in login_response.text:
            print("   ❌ Login failed: Invalid credentials")
        elif "Welcome back" in login_response.text:
            print("   ✅ Login successful (stayed on page)")
        else:
            print("   ❓ Login response unclear")
            
    elif login_response.status_code in [301, 302, 303, 307, 308]:
        # Login succeeded, got redirect
        redirect_to = login_response.headers.get('Location', 'Unknown')
        print(f"   ✅ Login successful - redirect to: {redirect_to}")
        
        # Check if session cookie was set
        if 'Set-Cookie' in login_response.headers:
            print("   ✅ Session cookie set")
        else:
            print("   ❌ No session cookie set")

if __name__ == "__main__":
    simple_login_test()
