#!/usr/bin/env python3
"""
Azure Deployment Verification Test
Run this after deploying the admin fixes to Azure
"""

import requests
import json
import time

def test_azure_admin_fix():
    """Test that the Azure admin fix deployment worked"""
    
    print("=" * 70)
    print("AZURE ADMIN FIX VERIFICATION TEST")
    print("=" * 70)
    
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    session = requests.Session()
    
    print(f"🎯 Testing Azure environment: {base_url}")
    print(f"🔑 Using admin credentials: admin / YourSecureAdminPassword123!")
    
    # Test login and session token
    print("\n1. Testing Admin Login and Session Token:")
    print("-" * 50)
    
    # Login
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Login Status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        redirect = login_response.headers.get('Location', '')
        print(f"   Redirect: {redirect}")
        if '/admin' in redirect:
            print("   ✅ Login successful - redirecting to admin")
        else:
            print(f"   ❌ Unexpected redirect: {redirect}")
            return False
    else:
        print(f"   ❌ Login failed with status {login_response.status_code}")
        return False
    
    # Check session info
    session_response = session.get(f"{base_url}/debug/session-info")
    if session_response.status_code == 200:
        session_data = session_response.json()
        session_token = session_data.get('session_token')
        username = session_data.get('username')
        is_admin = session_data.get('is_admin')
        user_id = session_data.get('user_id')
        
        print(f"\n2. Session Information:")
        print("-" * 50)
        print(f"   Session Token: {'✅ Present' if session_token else '❌ Missing'}")
        print(f"   Username: {username}")
        print(f"   Is Admin: {is_admin}")
        print(f"   User ID: {user_id}")
        
        if not session_token:
            print("   ❌ Session token still missing - fix not working")
            return False
        else:
            print("   ✅ Session token present - fix successful!")
    else:
        print(f"   ❌ Could not get session info: {session_response.status_code}")
        return False
    
    # Test admin dashboard access
    print(f"\n3. Admin Dashboard Access Test:")
    print("-" * 50)
    
    dashboard_response = session.get(f"{base_url}/admin")
    if dashboard_response.status_code == 200:
        content = dashboard_response.text.lower()
        
        # Check for access denied messages
        if 'please log in to access' in content:
            print("   ❌ Still getting access denied message")
            return False
        elif 'admin dashboard' in content or 'admin panel' in content:
            print("   ✅ Admin dashboard accessible!")
        else:
            print("   ⚠️  Dashboard loaded but unclear if admin features available")
    else:
        print(f"   ❌ Dashboard access failed: {dashboard_response.status_code}")
        return False
    
    # Test admin sub-pages
    print(f"\n4. Admin Sub-Pages Test:")
    print("-" * 50)
    
    admin_pages = [
        ('/admin/users', 'User Management'),
        ('/admin/sessions', 'Session Management'),
    ]
    
    all_accessible = True
    for page_url, page_name in admin_pages:
        page_response = session.get(f"{base_url}{page_url}")
        if page_response.status_code == 200:
            if 'please log in' in page_response.text.lower():
                print(f"   ❌ {page_name}: Access denied")
                all_accessible = False
            else:
                print(f"   ✅ {page_name}: Accessible")
        else:
            print(f"   ❌ {page_name}: HTTP {page_response.status_code}")
            all_accessible = False
    
    if all_accessible:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Azure admin fix deployment successful!")
        print("✅ Admin login and dashboard fully functional!")
        return True
    else:
        print("\n❌ Some tests failed")
        print("❌ Additional fixes may be needed")
        return False

if __name__ == "__main__":
    print("Azure Admin Fix Verification Test")
    print("Run this after deploying the fixes to Azure")
    print()
    
    success = test_azure_admin_fix()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ VERIFICATION SUCCESSFUL - Azure admin login working!")
    else:
        print("❌ VERIFICATION FAILED - Additional fixes needed")
        print("\nCheck:")
        print("1. SQL script was executed successfully")
        print("2. Updated app.py was deployed")
        print("3. Environment variables are set correctly")
    print("=" * 70)
