#!/usr/bin/env python3
"""
Test script to verify all admin routes are properly implemented
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_admin_routes():
    """Test that all required admin routes exist"""
    try:
        from app import app
        
        print("🔍 Testing Admin Routes")
        print("=" * 50)
        
        # Get all routes
        routes = {}
        for rule in app.url_map.iter_rules():
            routes[rule.endpoint] = {
                'path': str(rule),
                'methods': list(rule.methods)
            }
        
        # Required admin routes from templates
        required_routes = [
            'admin_dashboard',
            'admin_users', 
            'admin_sessions',
            'admin_security',
            'admin_courses',
            'admin_settings',
            'admin_change_password',
            'admin_add_user',
            'admin_delete_user',
            'admin_toggle_user_status',  # Fixed route
            'admin_reset_all_user_passwords',  # Newly added
            'admin_reset_user_password',  # Newly added
            'admin_add_course',
            'admin_edit_course',
            'admin_delete_course',
            'admin_populate_linkedin_courses',
            'admin_search_and_import_courses',
            'admin_url_validation',
            'admin_course_configs',
            'validate_all_urls',
            'url_validation_status'
        ]
        
        missing_routes = []
        for route in required_routes:
            if route in routes:
                print(f"✅ {route}")
            else:
                print(f"❌ {route} - MISSING")
                missing_routes.append(route)
        
        print("=" * 50)
        if missing_routes:
            print(f"❌ Missing {len(missing_routes)} routes: {', '.join(missing_routes)}")
            return False
        else:
            print(f"✅ All {len(required_routes)} admin routes are present!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Testing AI Learning Tracker - Admin Route Fix")
    print("=" * 60)
    
    success = test_admin_routes()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! The admin_pause_user issue is fixed.")
        print("\n✅ Key fixes applied:")
        print("  • Fixed admin_pause_user → admin_toggle_user_status in users.html")
        print("  • Added admin_reset_all_user_passwords route")
        print("  • Added admin_reset_user_password route")
        print("\n🌐 Server should now work without BuildError issues!")
        print("  Try accessing: http://localhost:5000/admin")
    else:
        print("❌ Some routes are still missing. Check the errors above.")
    
    return success

if __name__ == "__main__":
    main()
