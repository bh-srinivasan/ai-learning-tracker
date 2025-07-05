#!/usr/bin/env python3
"""
Detailed test script to investigate login behavior after restart
"""
import requests
import time

# Azure application URL
AZURE_URL = "https://ai-learning-tracker-bharath.azurewebsites.net"

def detailed_login_test():
    """Detailed test of login behavior"""
    print("🔍 Detailed login test after restart...")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{AZURE_URL}/", timeout=30)
        print(f"📡 Home page status: {response.status_code}")
        print(f"📍 Home page URL: {response.url}")
        
        # Test login page
        login_page = requests.get(f"{AZURE_URL}/login", timeout=30)
        print(f"🔐 Login page status: {login_page.status_code}")
        
        # Attempt login with bharath
        session = requests.Session()
        login_data = {
            'username': 'bharath',
            'password': 'bharath'
        }
        
        print("🔄 Attempting login with bharath/bharath...")
        login_response = session.post(f"{AZURE_URL}/login", data=login_data, timeout=30, allow_redirects=True)
        
        print(f"✉️  Login response status: {login_response.status_code}")
        print(f"📍 Final URL after login: {login_response.url}")
        print(f"📄 Response contains 'dashboard': {'dashboard' in login_response.text}")
        print(f"📄 Response contains 'bharath': {'bharath' in login_response.text}")
        print(f"📄 Response contains 'Welcome': {'Welcome' in login_response.text}")
        print(f"📄 Response contains 'Login': {'Login' in login_response.text}")
        
        # Check if we're actually logged in by trying to access dashboard directly
        dashboard_response = session.get(f"{AZURE_URL}/dashboard", timeout=30)
        print(f"🏠 Dashboard direct access status: {dashboard_response.status_code}")
        print(f"📍 Dashboard URL: {dashboard_response.url}")
        
        if dashboard_response.status_code == 200 and "dashboard" in dashboard_response.url:
            print("✅ Successfully logged in and can access dashboard!")
            return True
        elif dashboard_response.status_code == 302 or "login" in dashboard_response.url:
            print("❌ Login failed - redirected to login page")
            return False
        else:
            print(f"⚠️  Unexpected dashboard response: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in detailed login test: {e}")
        return False

def main():
    print("=" * 60)
    print("🔬 DETAILED LOGIN TEST AFTER RESTART")
    print("=" * 60)
    
    # Wait a bit more for full restart
    print("⏳ Waiting additional 15 seconds for complete restart...")
    time.sleep(15)
    
    success = detailed_login_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ LOGIN TEST: SUCCESS - Users persist after restart!")
    else:
        print("❌ LOGIN TEST: ISSUES DETECTED")
    print("=" * 60)

if __name__ == "__main__":
    main()
