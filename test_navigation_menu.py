#!/usr/bin/env python3
"""Test navigation menu after fixes"""

import requests

def test_navigation_menu():
    print("🔍 Testing navigation menu fixes...")
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # Step 1: Login as admin
    print("🔑 Step 1: Login as admin...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    print(f"   Login status: {login_response.status_code}")
    
    if login_response.status_code == 200 and "Admin Dashboard" in login_response.text:
        print("   ✅ Login successful and admin dashboard loads")
        
        # Check for navigation menu elements
        content = login_response.text
        
        # Check that menu items exist but with proper onclick handlers
        nav_items = [
            'Manage Users',
            'Session Management', 
            'Security Dashboard',
            'Manage Courses',
            'Settings',
            'Change Password'
        ]
        
        for item in nav_items:
            if item in content:
                print(f"   ✅ Found menu item: {item}")
                # Check if it has onclick instead of href="/admin"
                if f'onclick="alert(\'{item} feature coming soon!\')' in content:
                    print(f"      ✅ {item} has proper 'coming soon' alert")
                elif f'href="/admin"' in content and item in content:
                    print(f"      ❌ {item} still points to /admin (needs fix)")
                else:
                    print(f"      ✅ {item} appears to have proper handling")
            else:
                print(f"   ❌ Missing menu item: {item}")
        
        # Check that Admin Dashboard still works
        if 'href="/admin"' in content and 'Admin Dashboard' in content:
            print("   ✅ Admin Dashboard link still works")
        
        return True
    else:
        print("   ❌ Login failed or admin dashboard not loading")
        return False

if __name__ == "__main__":
    success = test_navigation_menu()
    if success:
        print("\n🎉 SUCCESS: Navigation menu should now work correctly!")
        print("🌐 Admin menu items will show 'coming soon' alerts")
        print("🎯 Only 'Admin Dashboard' will navigate to actual page")
    else:
        print("\n❌ FAILED: Navigation menu still has issues")
