#!/usr/bin/env python3
"""Test admin login and dashboard access"""

import requests
import os

def test_admin_login_flow():
    base_url = "http://localhost:5000"
    
    print("🔍 Testing admin login flow...")
    
    # Create session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Get login page
        print("📝 Step 1: Getting login page...")
        login_page = session.get(f"{base_url}/login")
        print(f"   Login page status: {login_page.status_code}")
        
        # Step 2: Login as admin
        print("🔑 Step 2: Logging in as admin...")
        
        # Try the common password from scripts
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        
        login_data = {
            'username': 'admin',
            'password': admin_password
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        print(f"   Login response status: {login_response.status_code}")
        print(f"   Login response URL: {login_response.url}")
        
        # Step 3: Access admin dashboard
        print("📊 Step 3: Accessing admin dashboard...")
        dashboard_response = session.get(f"{base_url}/admin")
        print(f"   Dashboard status: {dashboard_response.status_code}")
        print(f"   Dashboard URL: {dashboard_response.url}")
        
        # Check for error messages in response
        if "Database error occurred" in dashboard_response.text:
            print("❌ Found 'Database error occurred' in dashboard response!")
            
            # Look for specific error patterns
            if "Please check the logs" in dashboard_response.text:
                print("❌ Error message: 'Please check the logs' found")
        else:
            print("✅ No database error found in dashboard")
            
        # Check if we got redirected (might indicate session issue)
        if dashboard_response.url != f"{base_url}/admin":
            print(f"🔄 Redirected to: {dashboard_response.url}")
            
        return dashboard_response.text
        
    except requests.ConnectionError:
        print("❌ Cannot connect to Flask app. Is it running on localhost:5000?")
        return None
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return None

if __name__ == "__main__":
    result = test_admin_login_flow()
    if result:
        print(f"\n📄 Response length: {len(result)} characters")
        
        # Look for key indicators
        if "<title>" in result:
            title_start = result.find("<title>") + 7
            title_end = result.find("</title>")
            if title_start > 6 and title_end > title_start:
                print(f"📋 Page title: {result[title_start:title_end]}")
