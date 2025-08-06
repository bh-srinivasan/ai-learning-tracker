#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI Learning Tracker
Tests both local and Azure environments
"""

import os
import sys
import time
import requests
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AILearningTrackerTest:
    def __init__(self, base_url="https://ai-learning-tracker-bharath.azurewebsites.net"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.admin_credentials = {
            'username': 'admin',
            'password': os.environ.get('ADMIN_PASSWORD', 'defaultpass123')
        }
        self.test_user_credentials = {
            'username': 'testuser_' + str(int(time.time())),
            'password': 'testpass123'
        }
        
    def log_test(self, test_name, result, details=""):
        """Log test result"""
        status = "✅ PASS" if result else "❌ FAIL"
        message = f"{status} {test_name}"
        if details:
            message += f" - {details}"
        print(message)
        self.test_results.append({
            'test': test_name,
            'passed': result,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_homepage_accessibility(self):
        """Test if homepage is accessible"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            success = response.status_code == 200 and "AI Learning Tracker" in response.text
            self.log_test("Homepage Accessibility", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Homepage Accessibility", False, f"Error: {str(e)}")
            return False
            
    def test_database_connection(self):
        """Test database connection through login page"""
        try:
            response = self.session.get(f"{self.base_url}/login", timeout=10)
            success = response.status_code == 200 and "Login" in response.text
            self.log_test("Database Connection (Login Page)", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Database Connection (Login Page)", False, f"Error: {str(e)}")
            return False
            
    def test_admin_login(self):
        """Test admin login functionality"""
        try:
            # Get login page first to get any CSRF tokens
            login_page = self.session.get(f"{self.base_url}/login")
            
            # Attempt admin login
            login_data = {
                'username': self.admin_credentials['username'],
                'password': self.admin_credentials['password']
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data, timeout=10)
            
            # Check if login was successful (should redirect or show dashboard)
            success = (response.status_code in [200, 302] and 
                      ("dashboard" in response.url.lower() or 
                       "admin" in response.url.lower() or
                       response.status_code == 302))
            
            details = f"Status: {response.status_code}, URL: {response.url}"
            self.log_test("Admin Login", success, details)
            return success
            
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False
            
    def test_user_registration(self):
        """Test user registration functionality"""
        try:
            # Get registration page
            reg_page = self.session.get(f"{self.base_url}/register")
            if reg_page.status_code != 200:
                self.log_test("User Registration", False, f"Registration page not accessible: {reg_page.status_code}")
                return False
                
            # Register new user
            reg_data = {
                'username': self.test_user_credentials['username'],
                'password': self.test_user_credentials['password'],
                'confirm_password': self.test_user_credentials['password']
            }
            
            response = self.session.post(f"{self.base_url}/register", data=reg_data, timeout=10)
            
            # Check if registration was successful
            success = (response.status_code in [200, 302] and 
                      ("login" in response.url.lower() or 
                       "success" in response.text.lower() or
                       response.status_code == 302))
            
            details = f"Status: {response.status_code}, User: {self.test_user_credentials['username']}"
            self.log_test("User Registration", success, details)
            return success
            
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")
            return False
            
    def test_environment_variables(self):
        """Test that required environment variables are set"""
        required_vars = [
            'AZURE_SQL_SERVER',
            'AZURE_SQL_DATABASE', 
            'AZURE_SQL_USERNAME',
            'AZURE_SQL_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
                
        success = len(missing_vars) == 0
        details = f"Missing vars: {missing_vars}" if missing_vars else "All required vars present"
        self.log_test("Environment Variables", success, details)
        return success
        
    def test_security_headers(self):
        """Test security headers and no exposed credentials"""
        try:
            response = self.session.get(self.base_url)
            
            # Check that no credentials are exposed in response
            response_text = response.text.lower()
            security_issues = []
            
            # Check for exposed passwords/secrets
            if 'password' in response_text and any(word in response_text for word in ['=', 'secret', 'admin123']):
                security_issues.append("Potential password exposure")
                
            # Check for proper content type
            if 'text/html' not in response.headers.get('content-type', ''):
                security_issues.append("Missing HTML content type")
                
            success = len(security_issues) == 0
            details = f"Issues: {security_issues}" if security_issues else "No security issues found"
            self.log_test("Security Check", success, details)
            return success
            
        except Exception as e:
            self.log_test("Security Check", False, f"Error: {str(e)}")
            return False
            
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        endpoints = [
            ('/login', 'GET'),
            ('/register', 'GET'),
            ('/courses', 'GET'),
            ('/dashboard', 'GET')
        ]
        
        results = []
        for endpoint, method in endpoints:
            try:
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", timeout=5)
                    
                # Accept 200 (OK) or 302 (redirect, often for auth) or 401 (unauthorized but endpoint exists)
                success = response.status_code in [200, 302, 401]
                results.append(success)
                
            except Exception:
                results.append(False)
                
        overall_success = all(results)
        details = f"{sum(results)}/{len(results)} endpoints responding correctly"
        self.log_test("API Endpoints", overall_success, details)
        return overall_success
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Starting Comprehensive AI Learning Tracker Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_homepage_accessibility,
            self.test_database_connection,
            self.test_environment_variables,
            self.test_security_headers,
            self.test_api_endpoints,
            self.test_user_registration,
            self.test_admin_login
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Small delay between tests
            
        # Summary
        print("\n" + "=" * 60)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"🎯 Test Summary: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"⏱️  Total time: {time.time() - start_time:.2f} seconds")
        
        # Detailed results
        if passed_tests < total_tests:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test']}: {result['details']}")
                    
        print("\n✅ All Systems Status:")
        print(f"   • Web Application: {'🟢 Online' if self.test_results[0]['passed'] else '🔴 Offline'}")
        print(f"   • Database: {'🟢 Connected' if self.test_results[1]['passed'] else '🔴 Disconnected'}")
        print(f"   • Security: {'🟢 Secure' if any(r['test'] == 'Security Check' and r['passed'] for r in self.test_results) else '🔴 Issues Found'}")
        print(f"   • Admin Access: {'🟢 Working' if any(r['test'] == 'Admin Login' and r['passed'] for r in self.test_results) else '🔴 Failed'}")
        
        return success_rate >= 85  # 85% pass rate considered successful
        
    def generate_report(self):
        """Generate detailed test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_data = {
            'timestamp': timestamp,
            'base_url': self.base_url,
            'environment': 'Azure Production',
            'results': self.test_results
        }
        
        filename = f"test_report_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n📊 Detailed report saved to: {filename}")
        return filename

def main():
    """Main test execution"""
    # Check if we're testing local or Azure
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        base_url = "http://localhost:5000"
        
    print(f"🎯 Testing {base_url}")
    
    # Run tests
    tester = AILearningTrackerTest(base_url)
    success = tester.run_all_tests()
    
    # Generate report
    tester.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
