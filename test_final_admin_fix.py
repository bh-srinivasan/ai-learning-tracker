#!/usr/bin/env python3
"""Test admin dashboard access after template fix"""

import requests

def test_admin_dashboard_access():
    print("🔍 Testing admin dashboard access after template fix...")
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # Step 1: Login
    print("🔑 Step 1: Login as admin...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Login status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("   ✅ Login successful")
        
        # Step 2: Access admin dashboard
        print("📊 Step 2: Access admin dashboard...")
        admin_response = session.get(f"{base_url}/admin", allow_redirects=False)
        print(f"   Admin status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            print("   ✅ Admin dashboard loaded successfully!")
            
            # Check for errors in content
            content = admin_response.text
            if "Database error occurred" in content:
                print("   ❌ Still shows database error")
                return False
            elif "Admin Dashboard" in content:
                print("   ✅ Admin dashboard content loaded properly")
                
                # Check for specific admin elements
                if "Total Users" in content and "Total Courses" in content:
                    print("   ✅ Admin statistics are displayed")
                if "Quick Actions" in content:
                    print("   ✅ Quick Actions section loaded")
                if "Recent Users" in content:
                    print("   ✅ Recent Users section loaded")
                
                return True
            else:
                print("   ❓ Unexpected content in admin dashboard")
                return False
                
        elif admin_response.status_code == 302:
            redirect_to = admin_response.headers.get('Location', 'Unknown')
            print(f"   🔄 Redirected to: {redirect_to}")
            if '/login' in redirect_to:
                print("   ❌ Still redirecting to login - session issue remains")
            return False
        else:
            print(f"   ❌ Unexpected status code: {admin_response.status_code}")
            return False
    else:
        print("   ❌ Login failed")
        return False

if __name__ == "__main__":
    success = test_admin_dashboard_access()
    if success:
        print("\n🎉 SUCCESS: Admin dashboard is now working!")
        print("🌐 You can access it at: http://localhost:5000/admin")
        print("🔑 Login with: admin / YourSecureAdminPassword123!")
    else:
        print("\n❌ FAILED: Admin dashboard still has issues")
        print("Check the Flask app logs for more details")
