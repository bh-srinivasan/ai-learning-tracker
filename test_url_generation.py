#!/usr/bin/env python3
"""
Test Flask URL generation for admin routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_url_generation():
    """Test that all admin URLs can be generated correctly"""
    print("🔍 Testing Flask URL generation for admin routes...")
    
    admin_routes = [
        'admin_dashboard',
        'admin_users',
        'admin_sessions', 
        'admin_security',
        'admin_courses',
        'admin_settings',
        'admin_change_password'
    ]
    
    results = {}
    
    with app.app_context():
        for route_name in admin_routes:
            try:
                from flask import url_for
                url = url_for(route_name)
                results[route_name] = f"✅ {url}"
            except Exception as e:
                results[route_name] = f"❌ Error: {e}"
    
    print("\n📊 URL Generation Results:")
    print("=" * 60)
    
    success_count = 0
    for route_name, result in results.items():
        print(f"{route_name:<20} {result}")
        if "✅" in result:
            success_count += 1
    
    print("=" * 60)
    print(f"✅ {success_count}/{len(admin_routes)} URLs can be generated")
    
    if success_count == len(admin_routes):
        print("\n🎉 ALL ADMIN URLs CAN BE GENERATED!")
        print("The navigation menu should work correctly now.")
        return True
    else:
        print(f"\n⚠️  {len(admin_routes) - success_count} URLs have generation issues")
        return False

if __name__ == "__main__":
    success = test_url_generation()
    sys.exit(0 if success else 1)
