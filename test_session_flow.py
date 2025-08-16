#!/usr/bin/env python3
"""
Test login with session tracking using requests
"""
import requests
import json
import time

def test_azure_login_with_session():
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    session = requests.Session()
    
    print("🔐 Testing Azure Login Flow with Session Tracking")
    print("=" * 50)
    
    # Step 1: Get login page and extract any CSRF tokens
    print("1. Getting login page...")
    login_page = session.get(f"{base_url}/login")
    print(f"   Status: {login_page.status_code}")
    print(f"   Cookies after login page: {dict(session.cookies)}")
    
    # Step 2: Submit login form
    print("2. Submitting login form...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Status: {login_response.status_code}")
    print(f"   Headers: {dict(login_response.headers)}")
    print(f"   Cookies after login: {dict(session.cookies)}")
    
    if login_response.status_code == 302:
        redirect_url = login_response.headers.get('Location', '')
        print(f"   ✅ Login redirect to: {redirect_url}")
        
        # Step 3: Follow redirect to admin dashboard
        print("3. Following redirect to admin dashboard...")
        if redirect_url.startswith('/'):
            admin_url = f"{base_url}{redirect_url}"
        else:
            admin_url = redirect_url
            
        admin_response = session.get(admin_url)
        print(f"   Admin page status: {admin_response.status_code}")
        print(f"   Cookies for admin request: {dict(session.cookies)}")
        
        if admin_response.status_code == 500:
            print("   ❌ 500 Internal Server Error on admin page")
            print(f"   Response preview: {admin_response.text[:200]}...")
        elif admin_response.status_code == 200:
            print("   ✅ Admin page loaded successfully")
            print(f"   Content preview: {admin_response.text[:200]}...")
        else:
            print(f"   ⚠️ Unexpected status: {admin_response.status_code}")
            
    # Step 4: Check debug session endpoint with our session
    print("4. Checking debug session with our cookies...")
    debug_response = session.get(f"{base_url}/debug-session")
    print(f"   Debug status: {debug_response.status_code}")
    if debug_response.status_code == 200:
        try:
            debug_data = debug_response.json()
            print(f"   Session in memory: {debug_data.get('session_in_memory', 'N/A')}")
            print(f"   Session token: {debug_data.get('session_token', 'N/A')}")
            print(f"   Memory count: {debug_data.get('session_memory_count', 'N/A')}")
        except:
            print(f"   Debug response: {debug_response.text[:200]}...")

if __name__ == "__main__":
    test_azure_login_with_session()
