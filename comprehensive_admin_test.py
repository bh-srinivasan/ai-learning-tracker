#!/usr/bin/env python3
"""
Comprehensive test for all admin routes and URL generation
"""

import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_admin_routes():
    """Test all admin routes to ensure they exist and respond"""
    base_url = "http://127.0.0.1:5000"
    
    # Complete list of admin routes that should exist
    admin_routes = [
        # Basic admin pages
        '/admin',
        '/admin/users', 
        '/admin/sessions',
        '/admin/security',
        '/admin/courses',
        '/admin/settings',
        '/admin/change-password',
        
        # User management
        '/admin/add-user',
        
        # Course management  
        '/admin/add-course',
    ]
    
    # POST-only routes (we'll test with wrong method to confirm they exist)
    post_only_routes = [
        '/admin/reset-all-user-passwords',
        '/admin/reset-user-password', 
        '/admin/bulk-delete-courses',
    ]
    
    print("🔍 Testing admin GET routes availability...")
    
    # Test GET routes
    results = {}
    for route in admin_routes:
        try:
            url = f"{base_url}{route}"
            response = requests.get(url, timeout=5, allow_redirects=False)
            
            # We expect either:
            # - 200 (if logged in as admin)
            # - 302 (redirect to login - expected when not authenticated)
            # - 401/403 (unauthorized - also expected)
            if response.status_code in [200, 302, 401, 403]:
                results[route] = f"✅ Route exists (Status: {response.status_code})"
            else:
                results[route] = f"⚠️  Unexpected status: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            results[route] = "❌ Connection error - Flask app not running?"
        except Exception as e:
            results[route] = f"❌ Error: {e}"
    
    # Test POST-only routes (expect 405 Method Not Allowed when using GET)
    print("🔍 Testing admin POST-only routes...")
    for route in post_only_routes:
        try:
            url = f"{base_url}{route}"
            response = requests.get(url, timeout=5, allow_redirects=False)
            
            # For POST-only routes, we expect 405 (Method Not Allowed) when using GET
            # or 302 (redirect) if auth check happens first
            if response.status_code in [405, 302, 401, 403]:
                results[route] = f"✅ POST route exists (Status: {response.status_code})"
            else:
                results[route] = f"⚠️  Unexpected status: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            results[route] = "❌ Connection error - Flask app not running?"
        except Exception as e:
            results[route] = f"❌ Error: {e}"
    
    # Print results
    print("\n📊 Admin Route Test Results:")
    print("=" * 60)
    
    success_count = 0
    total_routes = len(admin_routes) + len(post_only_routes)
    
    for route, result in results.items():
        print(f"{route:<30} {result}")
        if "✅" in result:
            success_count += 1
    
    print("=" * 60)
    print(f"✅ {success_count}/{total_routes} routes are accessible")
    
    return success_count == total_routes

def test_url_generation():
    """Test Flask URL generation by checking if the routes exist in app.py"""
    print("\n🔍 Testing Flask route function names...")
    
    expected_functions = [
        'admin_dashboard',
        'admin_users',
        'admin_sessions', 
        'admin_security',
        'admin_courses',
        'admin_settings',
        'admin_change_password',
        'admin_add_user',
        'admin_add_course',
        'admin_reset_all_user_passwords',
        'admin_reset_user_password',
        'admin_bulk_delete_courses',
    ]
    
    # Read app.py and check for function definitions
    app_content = ""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
    except Exception as e:
        print(f"❌ Could not read app.py: {e}")
        return False
    
    results = {}
    for func_name in expected_functions:
        if f"def {func_name}(" in app_content:
            results[func_name] = "✅ Function exists"
        else:
            results[func_name] = "❌ Function missing"
    
    print("\n📊 Route Function Test Results:")
    print("=" * 60)
    
    success_count = 0
    for func_name, result in results.items():
        print(f"{func_name:<30} {result}")
        if "✅" in result:
            success_count += 1
    
    print("=" * 60)
    print(f"✅ {success_count}/{len(expected_functions)} functions exist")
    
    return success_count == len(expected_functions)

def test_templates_exist():
    """Test if required admin templates exist"""
    print("\n🔍 Testing admin templates...")
    
    required_templates = [
        'templates/admin/index.html',
        'templates/admin/users.html',
        'templates/admin/sessions.html',
        'templates/admin/security.html', 
        'templates/admin/courses.html',
        'templates/admin/settings.html',
        'templates/admin/change_password.html',
        'templates/admin/add_user.html',
        'templates/admin/add_course.html',
    ]
    
    results = {}
    for template in required_templates:
        if os.path.exists(template):
            results[template] = "✅ Template exists"
        else:
            results[template] = "❌ Template missing"
    
    print("\n📊 Template Test Results:")
    print("=" * 60)
    
    success_count = 0
    for template, result in results.items():
        template_name = template.replace('templates/admin/', '')
        print(f"{template_name:<25} {result}")
        if "✅" in result:
            success_count += 1
    
    print("=" * 60)
    print(f"✅ {success_count}/{len(required_templates)} templates exist")
    
    return success_count == len(required_templates)

def main():
    """Main test function"""
    print("🚀 Comprehensive Admin Routes Test")
    print("=" * 60)
    
    routes_ok = test_admin_routes()
    functions_ok = test_url_generation()
    templates_ok = test_templates_exist()
    
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS:")
    print("=" * 60)
    print(f"Routes accessible:     {'✅ PASS' if routes_ok else '❌ FAIL'}")
    print(f"Functions exist:       {'✅ PASS' if functions_ok else '❌ FAIL'}")
    print(f"Templates exist:       {'✅ PASS' if templates_ok else '❌ FAIL'}")
    
    all_passed = routes_ok and functions_ok and templates_ok
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The admin navigation should work correctly now.")
        print("You can log in as admin and test the 'Manage Users' link.")
    else:
        print("\n⚠️ SOME TESTS FAILED!")
        print("Please fix the issues above before testing admin navigation.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
