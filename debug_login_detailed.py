#!/usr/bin/env python3
"""Debug login process step by step"""

import requests
import json

def debug_login_step_by_step():
    base_url = "http://localhost:5000"
    
    print("🔍 Debugging login process step by step...")
    
    session = requests.Session()
    
    try:
        # Step 1: Get login page and check for CSRF or other requirements
        print("📝 Step 1: Getting login page...")
        login_page = session.get(f"{base_url}/login")
        print(f"   Status: {login_page.status_code}")
        
        # Check if there's any CSRF token or special requirements
        if 'csrf' in login_page.text.lower() or 'token' in login_page.text.lower():
            print("   ⚠️  Possible CSRF token required")
        else:
            print("   ✅ No CSRF token detected")
            
        # Step 2: Submit login form
        print("🔑 Step 2: Submitting login form...")
        
        login_data = {
            'username': 'admin',
            'password': 'YourSecureAdminPassword123!'
        }
        
        # Use proper form submission
        login_response = session.post(
            f"{base_url}/login", 
            data=login_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f"{base_url}/login"
            },
            allow_redirects=False  # Don't follow redirects to see what happens
        )
        
        print(f"   Status: {login_response.status_code}")
        print(f"   Headers: {dict(login_response.headers)}")
        
        # Check for redirect
        if login_response.status_code in [301, 302, 303, 307, 308]:
            print(f"   🔄 Redirect to: {login_response.headers.get('Location')}")
        
        # Check for flash messages or errors in response
        if "Invalid username or password" in login_response.text:
            print("   ❌ Login failed: Invalid credentials message found")
        elif "Welcome back" in login_response.text:
            print("   ✅ Login success message found")
        
        # Step 3: Follow redirect if any
        if login_response.status_code in [301, 302, 303, 307, 308]:
            print("📊 Step 3: Following redirect...")
            redirect_location = login_response.headers.get('Location')
            if redirect_location.startswith('/'):
                redirect_url = base_url + redirect_location
            else:
                redirect_url = redirect_location
                
            final_response = session.get(redirect_url, allow_redirects=False)
            print(f"   Final status: {final_response.status_code}")
            print(f"   Final URL attempted: {redirect_url}")
            
            if final_response.status_code in [301, 302, 303, 307, 308]:
                print(f"   🔄 Another redirect to: {final_response.headers.get('Location')}")
            elif "Database error occurred" in final_response.text:
                print("   ❌ Database error found after redirect!")
            else:
                print("   ✅ Page loaded after redirect")
        
        # Step 4: Try to access admin page directly
        print("🎯 Step 4: Direct admin page access...")
        admin_response = session.get(f"{base_url}/admin")
        print(f"   Admin page status: {admin_response.status_code}")
        print(f"   Admin page URL: {admin_response.url}")
        
        if "Database error occurred" in admin_response.text:
            print("   ❌ Database error found in admin page")
        elif "Welcome" in admin_response.text and "admin" in admin_response.text.lower():
            print("   ✅ Admin page loaded successfully")
        elif admin_response.url.endswith('/login'):
            print("   🔄 Redirected back to login - session not working")
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")

if __name__ == "__main__":
    debug_login_step_by_step()
