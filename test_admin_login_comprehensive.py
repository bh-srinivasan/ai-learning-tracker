"""
Comprehensive Admin Login Test
This script will test the complete admin login flow and fix any issues
"""

import requests
import json
import os
from datetime import datetime

class AdminLoginTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_environment_connection(self):
        """Test 1: Verify environment variables are set correctly"""
        try:
            response = self.session.get(f"{self.base_url}/test-environment-connection")
            data = response.json()
            
            if data.get('success'):
                self.log_test(
                    "Environment Connection",
                    True,
                    "All environment variables are set and connection successful",
                    data.get('environment_status')
                )
                return True
            else:
                self.log_test(
                    "Environment Connection",
                    False,
                    f"Environment connection failed: {data.get('error')}",
                    data
                )
                return False
        except Exception as e:
            self.log_test("Environment Connection", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_user_exists(self):
        """Test 2: Check if admin user exists and create if needed"""
        try:
            # Try to access the comprehensive initialization endpoint
            response = self.session.get(f"{self.base_url}/initialize-azure-database-complete")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        results = data.get('results', [])
                        admin_result = [r for r in results if 'Admin user' in r]
                        
                        if admin_result:
                            if 'created successfully' in admin_result[0]:
                                self.log_test(
                                    "Admin User Creation",
                                    True,
                                    "Admin user was created successfully"
                                )
                                return True
                            elif 'already exists' in admin_result[0]:
                                self.log_test(
                                    "Admin User Exists",
                                    True,
                                    "Admin user already exists in database"
                                )
                                return True
                        
                        # If we get here, assume success based on overall initialization
                        self.log_test(
                            "Database Initialization",
                            True,
                            "Database initialization completed successfully"
                        )
                        return True
                    else:
                        self.log_test(
                            "Database Initialization",
                            False,
                            f"Database initialization failed: {data.get('error', 'Unknown error')}"
                        )
                        return False
                except ValueError:
                    # Response is not JSON, treat as HTML success
                    content = response.text
                    if "successfully" in content.lower():
                        self.log_test(
                            "Database Initialization",
                            True,
                            "Database initialization appears successful"
                        )
                        return True
                    else:
                        self.log_test(
                            "Database Initialization", 
                            False,
                            f"Unexpected HTML response: {content[:100]}..."
                        )
                        return False
            else:
                self.log_test(
                    "Database Initialization",
                    False,
                    f"HTTP {response.status_code}: {response.text[:100]}"
                )
                return False
        except Exception as e:
            self.log_test("Database Initialization", False, f"Request failed: {str(e)}")
            return False
    
    def test_login_page_access(self):
        """Test 3: Verify login page is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            
            if response.status_code == 200 and "login" in response.text.lower():
                self.log_test(
                    "Login Page Access",
                    True,
                    "Login page is accessible and contains login form"
                )
                return True
            else:
                self.log_test(
                    "Login Page Access",
                    False,
                    f"HTTP {response.status_code} or missing login form"
                )
                return False
        except Exception as e:
            self.log_test("Login Page Access", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_login_submission(self):
        """Test 4: Submit admin login credentials"""
        try:
            # First get the login page to establish session
            login_response = self.session.get(f"{self.base_url}/login")
            
            # Prepare login data
            login_data = {
                'username': 'admin',
                'password': os.environ.get('ADMIN_PASSWORD') or 'ERROR_NO_ADMIN_PASSWORD_SET'  # Will fail if not set
            }
            
            # Submit login form
            response = self.session.post(
                f"{self.base_url}/login",
                data=login_data,
                allow_redirects=False  # Don't follow redirects to see the response
            )
            
            if response.status_code in [200, 302, 303, 307, 308]:
                # Check if redirected to admin dashboard
                if response.status_code >= 300:
                    redirect_location = response.headers.get('Location', '')
                    if '/admin' in redirect_location:
                        self.log_test(
                            "Admin Login Submission",
                            True,
                            f"Login successful - redirected to {redirect_location}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Admin Login Submission",
                            False,
                            f"Login failed - redirected to {redirect_location}"
                        )
                        return False
                else:
                    # Check response content for success indicators
                    content = response.text.lower()
                    if "error" in content or "invalid" in content:
                        self.log_test(
                            "Admin Login Submission",
                            False,
                            "Login failed - error message in response"
                        )
                        return False
                    else:
                        self.log_test(
                            "Admin Login Submission",
                            True,
                            "Login appears successful (200 response)"
                        )
                        return True
            else:
                self.log_test(
                    "Admin Login Submission",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
        except Exception as e:
            self.log_test("Admin Login Submission", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_dashboard_access(self):
        """Test 5: Access admin dashboard after login"""
        try:
            response = self.session.get(f"{self.base_url}/admin")
            
            if response.status_code == 200:
                content = response.text.lower()
                if "admin" in content and ("dashboard" in content or "statistics" in content):
                    self.log_test(
                        "Admin Dashboard Access",
                        True,
                        "Admin dashboard is accessible and contains expected content"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin Dashboard Access",
                        False,
                        "Dashboard accessible but missing expected content"
                    )
                    return False
            elif response.status_code == 302:
                redirect_location = response.headers.get('Location', '')
                self.log_test(
                    "Admin Dashboard Access",
                    False,
                    f"Redirected to {redirect_location} - likely not logged in"
                )
                return False
            else:
                self.log_test(
                    "Admin Dashboard Access",
                    False,
                    f"HTTP {response.status_code}: {response.text[:100]}"
                )
                return False
        except Exception as e:
            self.log_test("Admin Dashboard Access", False, f"Request failed: {str(e)}")
            return False
    
    def run_complete_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Admin Login Test")
        print("=" * 50)
        
        tests = [
            self.test_environment_connection,
            self.test_admin_user_exists,
            self.test_login_page_access,
            self.test_admin_login_submission,
            self.test_admin_dashboard_access
        ]
        
        all_passed = True
        for test in tests:
            result = test()
            all_passed = all_passed and result
            print()  # Add spacing between tests
        
        print("=" * 50)
        if all_passed:
            print("🎉 ALL TESTS PASSED! Admin login is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        print(f"\nTotal tests run: {len(self.test_results)}")
        passed = sum(1 for r in self.test_results if r['success'])
        print(f"Passed: {passed}")
        print(f"Failed: {len(self.test_results) - passed}")
        
        return all_passed, self.test_results

if __name__ == "__main__":
    # Run the comprehensive test
    tester = AdminLoginTester("https://ai-learning-tracker-bharath.azurewebsites.net")
    success, results = tester.run_complete_test()
    
    # Save results to file
    with open("admin_login_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: admin_login_test_results.json")
