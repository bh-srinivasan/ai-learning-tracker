#!/usr/bin/env python3
"""
Test script to identify and debug the login form submission error
This script will test the login functionality both locally and on Azure
"""

import requests
import json
import time
from datetime import datetime
import sys

class LoginTester:
    def __init__(self):
        self.azure_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
        self.local_url = "http://localhost:5000"
        self.session = requests.Session()
        
    def test_login_flow(self, base_url, username="admin", password=None):
        """Test the complete login flow"""
        print(f"\n{'='*50}")
        print(f"Testing Login Flow: {base_url}")
        print(f"{'='*50}")
        
        try:
            # Step 1: Get login page
            print("1. Getting login page...")
            login_page_response = self.session.get(f"{base_url}/login")
            print(f"   Status: {login_page_response.status_code}")
            
            if login_page_response.status_code != 200:
                print(f"   ❌ Failed to load login page")
                return False
            
            print(f"   ✅ Login page loaded successfully")
            
            # Step 2: Check if form exists
            if 'name="username"' not in login_page_response.text:
                print("   ❌ Username field not found in login form")
                return False
            
            if 'name="password"' not in login_page_response.text:
                print("   ❌ Password field not found in login form")
                return False
                
            print("   ✅ Login form fields found")
            
            # Step 3: Attempt login (if password provided)
            if password:
                print(f"2. Attempting login with username: {username}")
                
                login_data = {
                    'username': username,
                    'password': password
                }
                
                # Submit login form
                login_response = self.session.post(
                    f"{base_url}/login", 
                    data=login_data,
                    allow_redirects=False
                )
                
                print(f"   Status: {login_response.status_code}")
                print(f"   Headers: {dict(login_response.headers)}")
                
                if login_response.status_code == 500:
                    print("   ❌ Internal Server Error during login")
                    print(f"   Response text: {login_response.text[:500]}...")
                    return False
                elif login_response.status_code in [302, 303]:
                    print("   ✅ Login successful (redirect)")
                    location = login_response.headers.get('Location', '')
                    print(f"   Redirect to: {location}")
                    return True
                elif login_response.status_code == 200:
                    # Check if we're still on login page (failed login)
                    if 'Sign in to continue' in login_response.text:
                        print("   ❌ Login failed - still on login page")
                        return False
                    else:
                        print("   ✅ Login successful (same page)")
                        return True
                else:
                    print(f"   ❓ Unexpected status code: {login_response.status_code}")
                    return False
            else:
                print("2. Skipping login attempt (no password provided)")
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
    
    def test_database_connection(self, base_url):
        """Test if we can reach any database-dependent endpoint"""
        print(f"\n3. Testing database connectivity...")
        
        try:
            # Try to access a simple endpoint that might use database
            response = self.session.get(f"{base_url}/")
            print(f"   Homepage status: {response.status_code}")
            
            if response.status_code == 500:
                print("   ❌ Database connection issue detected")
                return False
            else:
                print("   ✅ Basic connectivity working")
                return True
                
        except Exception as e:
            print(f"   ❌ Error testing database: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print(f"AI Learning Tracker Login Test")
        print(f"Test started at: {datetime.now()}")
        
        # Test Azure deployment
        azure_success = False
        print(f"\n🌐 Testing Azure Deployment:")
        azure_success = self.test_login_flow(self.azure_url)
        self.test_database_connection(self.azure_url)
        
        # Prompt for admin password to test actual login
        print(f"\n🔑 To test actual login submission, we need the admin password.")
        print(f"    You can skip this by pressing Enter.")
        admin_password = input("Enter admin password (or press Enter to skip): ").strip()
        
        if admin_password:
            print(f"\n🔐 Testing Azure Login with Credentials:")
            login_success = self.test_login_flow(self.azure_url, "admin", admin_password)
            
            if login_success:
                # Test if we can access the admin dashboard after login
                print(f"\n📊 Testing Admin Dashboard Access:")
                try:
                    admin_response = self.session.get(f"{self.azure_url}/admin")
                    print(f"   Admin dashboard status: {admin_response.status_code}")
                    
                    if admin_response.status_code == 500:
                        print("   ❌ Internal Server Error when accessing admin dashboard")
                        print(f"   Response preview: {admin_response.text[:300]}...")
                        return False
                    elif admin_response.status_code == 200:
                        print("   ✅ Admin dashboard accessible")
                        return True
                    else:
                        print(f"   ❓ Unexpected admin dashboard status: {admin_response.status_code}")
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Error accessing admin dashboard: {e}")
                    return False
        
        # Summary
        print(f"\n{'='*50}")
        print(f"TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Azure Login Page: {'✅ PASS' if azure_success else '❌ FAIL'}")
        
        if not azure_success:
            print(f"\n🚨 ISSUES FOUND:")
            print(f"   - Azure login page has issues")
            print(f"   - Check Azure App Service logs for details")
        
        return azure_success

def main():
    """Main test function"""
    tester = LoginTester()
    success = tester.run_comprehensive_test()
    
    if not success:
        print(f"\n❌ Tests failed. Issues need to be resolved.")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
