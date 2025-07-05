#!/usr/bin/env python3
"""
Comprehensive test script to verify all fixes in the AI Learning Tracker
Uses environment variables for secure credential management
"""

import requests
import json
import time
import os
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AILearningTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
        # Get credentials from environment variables
        self.admin_password = os.environ.get('ADMIN_PASSWORD', 'fallback_admin')
        self.demo_password = os.environ.get('DEMO_PASSWORD', 'fallback_demo')
        
    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "✓ PASS" if success else "✗ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        print(f"{status}: {test_name} - {message}")
        
    def test_server_running(self):
        """Test if Flask server is running"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            success = response.status_code == 200
            self.log_test("Server Running", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Server Running", False, f"Error: {str(e)}")
            return False
            
    def test_admin_login(self):
        """Test admin login functionality"""
        try:
            # Get login page first
            login_url = urljoin(self.base_url, "/login")
            response = self.session.get(login_url)
            
            if response.status_code != 200:
                self.log_test("Admin Login", False, f"Login page error: {response.status_code}")
                return False
                
            # Attempt admin login using environment variable
            login_data = {
                'username': 'admin',
                'password': self.admin_password  # From environment variable
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=False)
            
            # Check for successful redirect (admin goes to /admin, users go to /dashboard)
            location = response.headers.get('Location', '')
            success = response.status_code in [302, 303] and ('/dashboard' in location or '/admin' in location)
            self.log_test("Admin Login", success, f"Status: {response.status_code}, Location: {location}")
            return success
            
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False
            
    def test_admin_dashboard(self):
        """Test admin dashboard access"""
        try:
            dashboard_url = urljoin(self.base_url, "/dashboard")
            response = self.session.get(dashboard_url)
            
            success = response.status_code == 200 and 'Admin Dashboard' in response.text
            self.log_test("Admin Dashboard", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Admin Dashboard", False, f"Error: {str(e)}")
            return False
            
    def test_admin_courses(self):
        """Test admin courses page"""
        try:
            courses_url = urljoin(self.base_url, "/admin/courses")
            response = self.session.get(courses_url)
            
            success = response.status_code == 200 and 'Manage Courses' in response.text
            self.log_test("Admin Courses Page", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Admin Courses Page", False, f"Error: {str(e)}")
            return False
            
    def test_admin_url_validation(self):
        """Test admin URL validation page"""
        try:
            url_validation_url = urljoin(self.base_url, "/admin/url-validation")
            response = self.session.get(url_validation_url)
            
            success = response.status_code == 200 and ('URL Validation' in response.text or 'validation' in response.text.lower())
            self.log_test("Admin URL Validation", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Admin URL Validation", False, f"Error: {str(e)}")
            return False
            
    def test_user_profile(self):
        """Test user profile page"""
        try:
            profile_url = urljoin(self.base_url, "/profile")
            response = self.session.get(profile_url)
            
            success = response.status_code == 200 and ('profile' in response.text.lower() or 'demo' in response.text.lower())
            self.log_test("User Profile Page", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("User Profile Page", False, f"Error: {str(e)}")
            return False
            
    def test_logout(self):
        """Test logout functionality"""
        try:
            logout_url = urljoin(self.base_url, "/logout")
            response = self.session.get(logout_url, allow_redirects=False)
            
            success = response.status_code in [302, 303]
            self.log_test("Logout", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Logout", False, f"Error: {str(e)}")
            return False
            
    def test_user_login(self):
        """Test regular user login"""
        try:
            # Get fresh session
            self.session = requests.Session()
            
            login_url = urljoin(self.base_url, "/login")
            login_data = {
                'username': 'demo',
                'password': self.demo_password  # From environment variable
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=False)
            success = response.status_code in [302, 303] and '/dashboard' in response.headers.get('Location', '')
            self.log_test("User Login", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return False
            
    def test_user_dashboard(self):
        """Test user dashboard"""
        try:
            dashboard_url = urljoin(self.base_url, "/dashboard")
            response = self.session.get(dashboard_url)
            
            success = response.status_code == 200 and 'dashboard' in response.text.lower()
            self.log_test("User Dashboard", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("User Dashboard", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("=" * 60)
        print("AI Learning Tracker - Comprehensive Test Suite")
        print("=" * 60)
        
        # Wait for server to be ready
        print("Waiting for server to start...")
        time.sleep(3)
        
        # Test server availability
        if not self.test_server_running():
            print("Server not running, aborting tests")
            return
            
        # Test admin functionality
        print("\n--- Testing Admin Functionality ---")
        self.test_admin_login()
        self.test_admin_dashboard()
        self.test_admin_courses()
        self.test_admin_url_validation()
        self.test_user_profile()  # Profile should work for admin too
        self.test_logout()
        
        # Test user functionality
        print("\n--- Testing User Functionality ---")
        self.test_user_login()
        self.test_user_dashboard()
        self.test_user_profile()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✓" if result['success'] else "✗"
            print(f"{status} {result['test']}")
            
        print(f"\nPassed: {passed}/{total} tests")
        
        if passed == total:
            print("🎉 All tests passed! The application is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
            
        return passed == total

if __name__ == "__main__":
    tester = AILearningTester()
    tester.run_all_tests()
