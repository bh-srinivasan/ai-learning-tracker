#!/usr/bin/env python3
"""
Test script to verify the new admin routes are properly implemented
"""

import sqlite3
from datetime import datetime
import os
import sys

# Add the current directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_routes():
    """Test that the new routes exist and are properly defined"""
    
    try:
        # Import the app
        from app import app
        
        print("✅ Successfully imported Flask app")
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        
        # Check for required admin routes
        required_routes = [
            'admin_populate_linkedin_courses',
            'admin_search_and_import_courses',
            'admin_settings',
            'admin_change_password',
            'admin_add_user',
            'admin_delete_user',
            'admin_toggle_user_status',
            'validate_all_urls',
            'url_validation_status'
        ]
        
        print("\n🔍 Checking required admin routes:")
        missing_routes = []
        
        for required_route in required_routes:
            found = False
            for route in routes:
                if route['endpoint'] == required_route:
                    print(f"  ✅ {required_route} - {route['path']} {route['methods']}")
                    found = True
                    break
            
            if not found:
                print(f"  ❌ {required_route} - MISSING")
                missing_routes.append(required_route)
        
        if missing_routes:
            print(f"\n❌ Missing routes: {missing_routes}")
            return False
        else:
            print(f"\n✅ All {len(required_routes)} required admin routes are present!")
            
        # Test database connectivity
        print("\n🗄️  Testing database connectivity:")
        try:
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            print(f"  ✅ Database connected, found {len(tables)} tables: {', '.join(tables)}")
        except Exception as e:
            print(f"  ❌ Database connection failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_validation_functionality():
    """Test the URL validation functionality"""
    print("\n🔗 Testing URL validation functionality:")
    
    try:
        # Test with a sample course
        from app import get_db_connection
        
        conn = get_db_connection()
        
        # Check if we have any courses to test with
        courses = conn.execute("SELECT COUNT(*) as count FROM courses").fetchone()
        print(f"  📚 Found {courses['count']} courses in database")
        
        # Check if URL status column exists
        try:
            conn.execute("SELECT url_status, last_url_check FROM courses LIMIT 1")
            print("  ✅ URL validation columns exist in database")
        except Exception as e:
            print(f"  ⚠️  URL validation columns missing: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Error testing URL validation: {e}")

def main():
    """Main test function"""
    print("🧪 Testing AI Learning Tracker - New Admin Routes")
    print("=" * 60)
    
    success = test_routes()
    test_url_validation_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application:")
        print("  python app.py")
        print("\nThen visit: http://localhost:5000")
        print("Admin login: admin / [check environment for password]")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    main()
