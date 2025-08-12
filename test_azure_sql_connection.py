import os
#!/usr/bin/env python3
"""
Comprehensive Azure SQL Database and Login Test
Tests the complete login flow on Azure with detailed error reporting
"""

import requests
import json
import time

def test_azure_comprehensive():
    """Comprehensive test of Azure SQL Database and login process"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("=" * 80)
    print("COMPREHENSIVE AZURE SQL DATABASE AND LOGIN TEST")
    print("=" * 80)
    
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': [],
        'overall_status': 'UNKNOWN'
    }
    
    # Use the admin password (value provided by user)
    # Password will be used to reset the admin user password in database
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    print("🔑 Using specified admin password...")
    print(f"✅ Admin password configured (length: {len(admin_password)})")
    
    print()
    
    try:
        # Test 1: Check if app is running and environment is correct
        print("📋 Test 1: Application Status and Environment Check")
        print("-" * 50)
        try:
            response = requests.get(f"{base_url}/debug/env", timeout=30)
            if response.status_code == 200:
                env_data = response.json()
                print("✅ App is running and responding")
                print(f"   Environment: {env_data.get('environment', 'unknown')}")
                print(f"   Azure SQL Server: {env_data.get('azure_sql_server', 'unknown')}")
                print(f"   Total Environment Variables: {env_data.get('total_env_vars', 'unknown')}")
                results['tests'].append({
                    'test': 'Application Status',
                    'status': 'PASS',
                    'details': env_data
                })
            else:
                print(f"❌ App status check failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Application Status',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                return results
        except Exception as e:
            print(f"❌ App status check error: {e}")
            results['tests'].append({
                'test': 'Application Status',
                'status': 'FAIL',
                'error': str(e)
            })
            return results
        
        print()
        
        # Test 2: Database Connection Test
        print("🗄️  Test 2: Database Connection Verification")
        print("-" * 50)
        try:
            response = requests.get(f"{base_url}/debug/db-test", timeout=30)
            if response.status_code == 200:
                db_data = response.json()
                print("✅ Database test endpoint accessible")
                
                for test in db_data.get('tests', []):
                    test_name = test.get('name', 'Unknown')
                    test_status = test.get('status', 'Unknown')
                    if test_status == 'PASS':
                        print(f"   ✅ {test_name}: {test.get('details', {}).get('message', 'Success')}")
                    else:
                        print(f"   ❌ {test_name}: {test.get('details', {}).get('error', 'Failed')}")
                
                results['tests'].append({
                    'test': 'Database Connection',
                    'status': 'PASS' if all(t['status'] == 'PASS' for t in db_data.get('tests', [])) else 'FAIL',
                    'details': db_data
                })
            else:
                print(f"❌ Database test failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Database Connection',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
        except Exception as e:
            print(f"❌ Database test error: {e}")
            results['tests'].append({
                'test': 'Database Connection',
                'status': 'FAIL',
                'error': str(e)
            })
        
        print()
        
        # Test 3: Route Registration Check
        print("🛣️  Test 3: Route Registration Verification")
        print("-" * 50)
        try:
            response = requests.get(f"{base_url}/debug/routes", timeout=30)
            if response.status_code == 200:
                routes_data = response.json()
                print(f"✅ Total routes registered: {routes_data.get('total_routes', 0)}")
                
                categories = routes_data.get('categories', {})
                for cat_name, cat_data in categories.items():
                    count = cat_data.get('count', 0)
                    print(f"   📁 {cat_name}: {count} routes")
                    
                    # Check key routes
                    if cat_name == 'admin_routes':
                        admin_routes = [r['rule'] for r in cat_data.get('routes', [])]
                        key_admin_routes = ['/admin', '/admin/users', '/admin/settings']
                        for key_route in key_admin_routes:
                            if key_route in admin_routes:
                                print(f"      ✅ {key_route} registered")
                            else:
                                print(f"      ❌ {key_route} missing")
                    
                    elif cat_name == 'auth_routes':
                        auth_routes = [r['rule'] for r in cat_data.get('routes', [])]
                        if '/login' in auth_routes:
                            print(f"      ✅ /login registered")
                        else:
                            print(f"      ❌ /login missing")
                
                results['tests'].append({
                    'test': 'Route Registration',
                    'status': 'PASS',
                    'details': routes_data
                })
            else:
                print(f"❌ Routes check failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Route Registration', 
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
        except Exception as e:
            print(f"❌ Routes check error: {e}")
            results['tests'].append({
                'test': 'Route Registration',
                'status': 'FAIL',
                'error': str(e)
            })
        
        print()
        
        # Test 4: Login Page Accessibility
        print("🔐 Test 4: Login Page Accessibility")
        print("-" * 50)
        try:
            response = requests.get(f"{base_url}/login", timeout=30)
            if response.status_code == 200:
                print("✅ Login page loads successfully")
                
                # Check for common error indicators in the page
                page_content = response.text.lower()
                error_indicators = ['database error', 'connection error', 'internal server error']
                
                errors_found = []
                for indicator in error_indicators:
                    if indicator in page_content:
                        errors_found.append(indicator)
                
                if errors_found:
                    print(f"❌ Errors found in login page: {', '.join(errors_found)}")
                    results['tests'].append({
                        'test': 'Login Page Accessibility',
                        'status': 'FAIL',
                        'error': f'Page contains errors: {errors_found}'
                    })
                else:
                    print("✅ No error indicators found in login page")
                    results['tests'].append({
                        'test': 'Login Page Accessibility',
                        'status': 'PASS',
                        'details': 'Login page loads without errors'
                    })
            else:
                print(f"❌ Login page failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Login Page Accessibility',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
        except Exception as e:
            print(f"❌ Login page error: {e}")
            results['tests'].append({
                'test': 'Login Page Accessibility',
                'status': 'FAIL',
                'error': str(e)
            })
        
        print()
        
        # Test 5: Comprehensive Login Process (Using Debug Endpoint)
        print("🧪 Test 5: Comprehensive Login Process Test")
        print("-" * 50)
        
        # Test with debug endpoint first to get detailed step-by-step results
        try:
            session = requests.Session()
            login_data = {
                'username': 'admin',
                'password': admin_password  # Using password from environment
            }
            
            print("   Testing with admin credentials via debug endpoint...")
            response = session.post(f"{base_url}/debug/login-test", 
                                  data=login_data, 
                                  timeout=30)
            
            if response.status_code == 200:
                debug_result = response.json()
                print("✅ Debug login test completed")
                
                # Analyze each step
                steps = debug_result.get('steps', [])
                for step in steps:
                    step_num = step.get('step', '?')
                    step_desc = step.get('description', 'Unknown')
                    step_status = step.get('status', 'Unknown')
                    
                    if step_status == 'PASS':
                        print(f"   ✅ Step {step_num}: {step_desc}")
                        if 'details' in step:
                            print(f"      Details: {step['details']}")
                    else:
                        print(f"   ❌ Step {step_num}: {step_desc}")
                        if 'error' in step:
                            print(f"      Error: {step['error']}")
                
                overall_status = debug_result.get('overall_status', 'UNKNOWN')
                if overall_status == 'SUCCESS':
                    print("✅ Overall login test: SUCCESS")
                    results['tests'].append({
                        'test': 'Comprehensive Login Process',
                        'status': 'PASS',
                        'details': debug_result
                    })
                else:
                    print(f"❌ Overall login test: {overall_status}")
                    results['tests'].append({
                        'test': 'Comprehensive Login Process',
                        'status': 'FAIL',
                        'details': debug_result
                    })
                    
            else:
                print(f"❌ Debug login test failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                results['tests'].append({
                    'test': 'Comprehensive Login Process',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ Debug login test error: {e}")
            results['tests'].append({
                'test': 'Comprehensive Login Process',
                'status': 'FAIL',
                'error': str(e)
            })
        
        print()
        
        # Test 6: Actual Login Flow Test
        print("🚀 Test 6: Actual Login Flow Test")
        print("-" * 50)
        
        try:
            session = requests.Session()
            login_data = {
                'username': 'admin',
                'password': admin_password  # Using password from environment
            }
            
            print("   Attempting actual login...")
            response = session.post(f"{base_url}/login", 
                                  data=login_data, 
                                  timeout=30,
                                  allow_redirects=False)
            
            print(f"   Login response status: {response.status_code}")
            
            if response.status_code == 302:
                # Successful redirect
                redirect_location = response.headers.get('Location', '')
                print(f"   ✅ Login successful - redirecting to: {redirect_location}")
                
                if '/admin' in redirect_location or '/dashboard' in redirect_location:
                    print("   ✅ Redirect target is appropriate for admin user")
                    results['tests'].append({
                        'test': 'Actual Login Flow',
                        'status': 'PASS',
                        'details': f'Redirected to {redirect_location}'
                    })
                else:
                    print(f"   ⚠️  Unexpected redirect target: {redirect_location}")
                    results['tests'].append({
                        'test': 'Actual Login Flow',
                        'status': 'WARNING',
                        'details': f'Unexpected redirect to {redirect_location}'
                    })
                    
            elif response.status_code == 200:
                # Stayed on login page - check for errors
                page_content = response.text.lower()
                if any(error in page_content for error in ['invalid', 'error', 'failed']):
                    print("   ❌ Login failed - credentials rejected or error occurred")
                    results['tests'].append({
                        'test': 'Actual Login Flow',
                        'status': 'FAIL',
                        'error': 'Login credentials rejected or error in login process'
                    })
                else:
                    print("   ⚠️  Login returned to form without clear error message")
                    results['tests'].append({
                        'test': 'Actual Login Flow',
                        'status': 'WARNING',
                        'details': 'Returned to login form without clear error'
                    })
                    
            elif response.status_code == 500:
                print("   ❌ Internal Server Error during login")
                results['tests'].append({
                    'test': 'Actual Login Flow',
                    'status': 'FAIL',
                    'error': 'Internal Server Error (500)'
                })
            else:
                print(f"   ❌ Unexpected response: {response.status_code}")
                results['tests'].append({
                    'test': 'Actual Login Flow',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ Actual login test error: {e}")
            results['tests'].append({
                'test': 'Actual Login Flow',
                'status': 'FAIL', 
                'error': str(e)
            })
        
        # Determine overall status
        test_statuses = [t['status'] for t in results['tests']]
        if all(status == 'PASS' for status in test_statuses):
            results['overall_status'] = 'ALL_PASS'
        elif any(status == 'FAIL' for status in test_statuses):
            results['overall_status'] = 'SOME_FAILURES'
        else:
            results['overall_status'] = 'MIXED_RESULTS'
        
        return results
        
    except Exception as e:
        print(f"❌ Comprehensive test error: {e}")
        results['overall_status'] = 'ERROR'
        results['error'] = str(e)
        return results

def main():
    """Main function"""
    print("Starting comprehensive Azure testing...")
    print()
    
    results = test_azure_comprehensive()
    
    print()
    print("=" * 80)
    print("FINAL RESULTS SUMMARY")
    print("=" * 80)
    
    # Print summary
    total_tests = len(results.get('tests', []))
    passed_tests = len([t for t in results.get('tests', []) if t['status'] == 'PASS'])
    failed_tests = len([t for t in results.get('tests', []) if t['status'] == 'FAIL'])
    warning_tests = len([t for t in results.get('tests', []) if t['status'] == 'WARNING'])
    
    print(f"📊 Test Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   ⚠️  Warnings: {warning_tests}")
    print()
    
    # Print individual test results
    for test in results.get('tests', []):
        test_name = test['test']
        test_status = test['status']
        status_icon = '✅' if test_status == 'PASS' else '❌' if test_status == 'FAIL' else '⚠️'
        print(f"{status_icon} {test_name}: {test_status}")
        
        if 'error' in test:
            print(f"    Error: {test['error']}")
        elif 'details' in test and isinstance(test['details'], str):
            print(f"    Details: {test['details']}")
    
    print()
    print(f"🎯 Overall Status: {results['overall_status']}")
    
    # Recommendations
    if results['overall_status'] == 'ALL_PASS':
        print("🎉 All tests passed! Azure SQL Database and login are working correctly.")
    elif failed_tests > 0:
        print("🔧 Issues found that need attention:")
        for test in results.get('tests', []):
            if test['status'] == 'FAIL':
                print(f"   - {test['test']}: {test.get('error', 'Failed')}")
        print()
        print("💡 Recommended next steps:")
        print("   1. Check Azure App Service logs for detailed error messages")
        print("   2. Verify admin user exists in the database")
        print("   3. Confirm password matches what's set in Azure environment variables")
        print("   4. Check Azure SQL Database firewall and connection settings")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
