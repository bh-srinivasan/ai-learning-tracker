#!/usr/bin/env python3
"""
Test script to verify all admin routes are working correctly
"""

import requests
import sys

def test_admin_routes():
    """Test all admin routes to ensure they exist and respond"""
    base_url = "http://127.0.0.1:5000"
    
    # List of admin routes that should exist
    admin_routes = [
        '/admin',
        '/admin/users', 
        '/admin/sessions',
        '/admin/security',
        '/admin/courses',
        '/admin/settings',
        '/admin/change-password'
    ]
    
    print("🔍 Testing admin routes availability...")
    
    # Test each route
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
        except requests.exceptions.RequestException as e:
            results[route] = f"❌ Request error: {e}"
        except Exception as e:
            results[route] = f"❌ Unexpected error: {e}"
    
    # Print results
    print("\n📊 Admin Route Test Results:")
    print("=" * 50)
    
    success_count = 0
    for route, result in results.items():
        print(f"{route:<25} {result}")
        if "✅" in result:
            success_count += 1
    
    print("=" * 50)
    print(f"✅ {success_count}/{len(admin_routes)} routes are accessible")
    
    if success_count == len(admin_routes):
        print("\n🎉 ALL ADMIN ROUTES ARE WORKING!")
        print("You can now navigate to http://127.0.0.1:5000 and test the admin navigation menu.")
        return True
    else:
        print(f"\n⚠️  {len(admin_routes) - success_count} routes have issues")
        return False

if __name__ == "__main__":
    success = test_admin_routes()
    sys.exit(0 if success else 1)
