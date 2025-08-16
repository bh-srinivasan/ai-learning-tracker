#!/usr/bin/env python3
"""
Simple test to call the admin endpoint with a valid session
"""
import requests
import json

def test_admin_directly():
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    session = requests.Session()
    
    print("🔐 Testing Admin Dashboard Directly")
    print("=" * 40)
    
    # Step 1: Login to get session
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    if login_response.status_code != 302:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    print("✅ Login successful")
    
    # Step 2: Try debug session
    debug_response = session.get(f"{base_url}/debug-session")
    print(f"Debug status: {debug_response.status_code}")
    
    if debug_response.status_code == 200:
        debug_data = debug_response.json()
        print(f"Session active: {debug_data.get('session_in_memory', False)}")
        print(f"Session token: {debug_data.get('session_token', 'None')}")
    
    # Step 3: Try admin page with custom error handling
    print("\n🎯 Testing admin page...")
    try:
        admin_response = session.get(f"{base_url}/admin", timeout=30)
        print(f"Admin status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            print("✅ SUCCESS! Admin dashboard loaded!")
            if "Admin Dashboard" in admin_response.text or "admin" in admin_response.text.lower():
                print("✅ Admin content detected")
            else:
                print("⚠️ Admin page loaded but content unclear")
                print(f"Content preview: {admin_response.text[:200]}...")
        else:
            print(f"❌ Admin failed with status: {admin_response.status_code}")
            print(f"Response: {admin_response.text[:300]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Admin request timed out")
    except Exception as e:
        print(f"❌ Admin request failed: {e}")

if __name__ == "__main__":
    test_admin_directly()
