import os
#!/usr/bin/env python3
"""
Comprehensive Admin Login and Dashboard Access Test
Tests the complete admin flow: login -> redirect -> dashboard access
"""

import requests
import json
import time
from urllib.parse import urljoin

def test_admin_login_and_dashboard():
    """Test complete admin login flow and dashboard access"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"  # Test Azure environment
    
    print("=" * 80)
    print("COMPREHENSIVE ADMIN LOGIN AND DASHBOARD ACCESS TEST")
    print("=" * 80)
    
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': [],
        'overall_status': 'UNKNOWN'
    }
    
    # Use session to maintain cookies
    session = requests.Session()
    
    print("🔑 Using admin credentials for testing...")
    admin_username = "admin"
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123!')  # Use the updated admin password
    
    try:
        # Test 1: Check login page loads
        print("\n📋 Test 1: Login Page Accessibility")
        print("-" * 50)
        try:
            response = session.get(f"{base_url}/login", timeout=30)
            if response.status_code == 200:
                print("✅ Login page loads successfully")
                results['tests'].append({
                    'test': 'Login Page Load',
                    'status': 'PASS'
                })
            else:
                print(f"❌ Login page failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Login Page Load',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                return results
        except Exception as e:
            print(f"❌ Login page error: {e}")
            results['tests'].append({
                'test': 'Login Page Load',
                'status': 'FAIL',
                'error': str(e)
            })
            return results

        # Test 2: Perform login and check redirect
        print("\n🚀 Test 2: Admin Login Process")
        print("-" * 50)
        try:
            login_data = {
                'username': admin_username,
                'password': admin_password
            }
            
            print("   Attempting login...")
            response = session.post(f"{base_url}/login", 
                                  data=login_data, 
                                  timeout=30,
                                  allow_redirects=False)
            
            print(f"   Login response status: {response.status_code}")
            
            if response.status_code == 302:
                redirect_location = response.headers.get('Location', '')
                print(f"   ✅ Login successful - redirecting to: {redirect_location}")
                
                # Check if redirect is to admin
                if '/admin' in redirect_location:
                    print("   ✅ Redirect target is admin dashboard")
                    results['tests'].append({
                        'test': 'Admin Login',
                        'status': 'PASS',
                        'details': f'Redirected to {redirect_location}'
                    })
                else:
                    print(f"   ❌ Unexpected redirect target: {redirect_location}")
                    results['tests'].append({
                        'test': 'Admin Login',
                        'status': 'FAIL',
                        'error': f'Unexpected redirect to {redirect_location}'
                    })
            elif response.status_code == 200:
                # Check if login failed
                page_content = response.text.lower()
                if any(error in page_content for error in ['invalid', 'error', 'failed']):
                    print("   ❌ Login failed - credentials rejected")
                    results['tests'].append({
                        'test': 'Admin Login',
                        'status': 'FAIL',
                        'error': 'Login credentials rejected'
                    })
                else:
                    print("   ❌ Login stayed on same page without clear error")
                    results['tests'].append({
                        'test': 'Admin Login',
                        'status': 'FAIL',
                        'error': 'No redirect occurred'
                    })
            else:
                print(f"   ❌ Unexpected login response: {response.status_code}")
                results['tests'].append({
                    'test': 'Admin Login',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ Login test error: {e}")
            results['tests'].append({
                'test': 'Admin Login',
                'status': 'FAIL',
                'error': str(e)
            })

        # Test 3: Access admin dashboard directly
        print("\n🏠 Test 3: Admin Dashboard Direct Access")
        print("-" * 50)
        try:
            print("   Accessing admin dashboard...")
            response = session.get(f"{base_url}/admin", timeout=30)
            
            print(f"   Dashboard response status: {response.status_code}")
            
            if response.status_code == 200:
                page_content = response.text
                
                # Check for error messages
                error_indicators = [
                    'please log in to access the admin panel',
                    'admin privileges required',
                    'session expired',
                    'please log in to access',
                    'login required'
                ]
                
                errors_found = []
                for indicator in error_indicators:
                    if indicator.lower() in page_content.lower():
                        errors_found.append(indicator)
                
                if errors_found:
                    print(f"   ❌ Admin dashboard shows access errors:")
                    for error in errors_found:
                        print(f"      - {error}")
                    
                    # Extract more context around the error
                    lines = page_content.split('\n')
                    for i, line in enumerate(lines):
                        for error in errors_found:
                            if error.lower() in line.lower():
                                print(f"      Context: {line.strip()}")
                    
                    results['tests'].append({
                        'test': 'Admin Dashboard Access',
                        'status': 'FAIL',
                        'error': f'Access denied: {", ".join(errors_found)}'
                    })
                else:
                    # Check for admin dashboard indicators
                    admin_indicators = [
                        'admin dashboard',
                        'manage users',
                        'user management',
                        'admin panel',
                        'system settings'
                    ]
                    
                    admin_found = []
                    for indicator in admin_indicators:
                        if indicator.lower() in page_content.lower():
                            admin_found.append(indicator)
                    
                    if admin_found:
                        print(f"   ✅ Admin dashboard loaded successfully")
                        print(f"      Found admin features: {', '.join(admin_found)}")
                        results['tests'].append({
                            'test': 'Admin Dashboard Access',
                            'status': 'PASS',
                            'details': f'Dashboard loaded with features: {", ".join(admin_found)}'
                        })
                    else:
                        print("   ⚠️  Dashboard loaded but no clear admin features found")
                        results['tests'].append({
                            'test': 'Admin Dashboard Access',
                            'status': 'WARNING',
                            'details': 'Dashboard loaded but admin features unclear'
                        })
                        
            elif response.status_code == 302:
                redirect_location = response.headers.get('Location', '')
                print(f"   ❌ Dashboard redirected to: {redirect_location}")
                if '/login' in redirect_location:
                    print("   ❌ Redirected back to login - session not maintained")
                    results['tests'].append({
                        'test': 'Admin Dashboard Access',
                        'status': 'FAIL',
                        'error': 'Redirected to login - session lost'
                    })
                else:
                    results['tests'].append({
                        'test': 'Admin Dashboard Access',
                        'status': 'FAIL',
                        'error': f'Unexpected redirect to {redirect_location}'
                    })
            else:
                print(f"   ❌ Dashboard access failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Admin Dashboard Access',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ Dashboard access error: {e}")
            results['tests'].append({
                'test': 'Admin Dashboard Access',
                'status': 'FAIL',
                'error': str(e)
            })

        # Test 4: Check session information via debug endpoint
        print("\n🔍 Test 4: Session Information Analysis")
        print("-" * 50)
        try:
            print("   Checking session status...")
            response = session.get(f"{base_url}/debug/session-info", timeout=30)
            
            if response.status_code == 200:
                session_data = response.json()
                print(f"   ✅ Session debug endpoint accessible")
                
                # Analyze session data
                session_token = session_data.get('session_token')
                username = session_data.get('username')
                is_admin = session_data.get('is_admin')
                user_id = session_data.get('user_id')
                
                print(f"      Session Token: {'Present' if session_token else 'Missing'}")
                print(f"      Username: {username or 'Missing'}")
                print(f"      Is Admin: {is_admin}")
                print(f"      User ID: {user_id or 'Missing'}")
                
                if session_token and username and is_admin:
                    print("   ✅ Session appears valid for admin access")
                    results['tests'].append({
                        'test': 'Session Information',
                        'status': 'PASS',
                        'details': f'Valid admin session for {username}'
                    })
                else:
                    print(f"   ❌ Session incomplete or invalid")
                    results['tests'].append({
                        'test': 'Session Information',
                        'status': 'FAIL',
                        'error': 'Session missing required admin data'
                    })
                    
            elif response.status_code == 404:
                print("   ⚠️  Session debug endpoint not available")
                results['tests'].append({
                    'test': 'Session Information',
                    'status': 'WARNING',
                    'details': 'Debug endpoint not available'
                })
            else:
                print(f"   ❌ Session check failed: {response.status_code}")
                results['tests'].append({
                    'test': 'Session Information',
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ Session check error: {e}")
            results['tests'].append({
                'test': 'Session Information',
                'status': 'FAIL',
                'error': str(e)
            })

        # Test 5: Test admin sub-pages
        print("\n📁 Test 5: Admin Sub-Pages Access")
        print("-" * 50)
        
        admin_pages = [
            ('/admin/users', 'User Management'),
            ('/admin/sessions', 'Session Management'),
            ('/admin/settings', 'Settings'),
            ('/admin/security', 'Security')
        ]
        
        for page_url, page_name in admin_pages:
            try:
                print(f"   Testing {page_name}...")
                response = session.get(f"{base_url}{page_url}", timeout=30)
                
                if response.status_code == 200:
                    page_content = response.text.lower()
                    if 'please log in' in page_content or 'admin privileges required' in page_content:
                        print(f"   ❌ {page_name}: Access denied")
                    else:
                        print(f"   ✅ {page_name}: Accessible")
                elif response.status_code == 302:
                    redirect = response.headers.get('Location', '')
                    if '/login' in redirect:
                        print(f"   ❌ {page_name}: Redirected to login")
                    else:
                        print(f"   ⚠️  {page_name}: Redirected to {redirect}")
                else:
                    print(f"   ❌ {page_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {page_name}: Error {e}")

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
    print("Starting comprehensive admin login and dashboard test...")
    print()
    
    results = test_admin_login_and_dashboard()
    
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
        print("🎉 All tests passed! Admin login and dashboard access working correctly.")
    elif failed_tests > 0:
        print("🔧 Issues found that need attention:")
        for test in results.get('tests', []):
            if test['status'] == 'FAIL':
                print(f"   - {test['test']}: {test.get('error', 'Failed')}")
        print()
        print("💡 Recommended next steps:")
        print("   1. Check admin dashboard route implementation")
        print("   2. Verify session management in admin routes")
        print("   3. Check admin privilege validation logic")
        print("   4. Review Flask session configuration")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
