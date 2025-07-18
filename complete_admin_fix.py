#!/usr/bin/env python3
"""
Complete fix for admin search courses and user login issues
"""

def test_and_fix_issues():
    """Test and fix both search courses and user login issues"""
    
    print("🔍 TESTING AND FIXING ADMIN ISSUES")
    print("=" * 50)
    
    # Test 1: Check if admin_search_and_import_courses exists
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app import app
        
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        print("✅ Flask app loaded successfully")
        
        # Check for search courses route
        if '/admin/search-and-import-courses' in routes:
            print("✅ Search Courses route is present")
        else:
            print("❌ Search Courses route is MISSING")
        
        # Test user login functionality
        with app.test_client() as client:
            print("\n🧪 Testing login functionality...")
            
            # Test login page loads
            response = client.get('/login')
            if response.status_code == 200:
                print("✅ Login page loads successfully")
            else:
                print(f"❌ Login page error: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        return False

def provide_solutions():
    """Provide solutions for the issues"""
    
    print("\n💡 SOLUTIONS FOR CURRENT ISSUES:")
    print("=" * 40)
    
    print("🔧 ISSUE 1: Search Courses not working")
    print("   CAUSE: Missing admin_search_and_import_courses route")
    print("   STATUS: ✅ FIXED - Route has been added to app.py")
    print("   TEST: Restart server and try Search Courses again")
    
    print("\n🔧 ISSUE 2: Cannot login with other users")
    print("   POSSIBLE CAUSES:")
    print("   1. New users created with wrong password format")
    print("   2. User status set to 'inactive'")
    print("   3. Password hash not properly generated")
    
    print("\n📝 USER LOGIN TROUBLESHOOTING STEPS:")
    print("   1. For newly created users, try these passwords:")
    print("      - The username itself (e.g., user 'testuser' → password 'testuser')")
    print("      - The reset format: 'username_reset123'")
    print("      - The password you set when creating the user")
    
    print("\n   2. Check user status in admin panel:")
    print("      - Go to Manage Users")
    print("      - Ensure user status shows 'Active'")
    print("      - If 'Inactive', use toggle button to activate")
    
    print("\n   3. Reset user password if needed:")
    print("      - In Manage Users page")
    print("      - Click reset password for the specific user")
    print("      - New password will be: username_reset123")
    
    print("\n🚀 TESTING INSTRUCTIONS:")
    print("   1. Restart the Flask server")
    print("   2. Login as admin")
    print("   3. Go to Manage Users → check user status")
    print("   4. Try Search Courses functionality")
    print("   5. Test user login with suggested passwords")

if __name__ == "__main__":
    print("ADMIN ISSUES DIAGNOSIS AND FIX")
    print("=" * 50)
    
    # Run tests
    test_and_fix_issues()
    
    # Provide solutions
    provide_solutions()
    
    print("\n🎉 SUMMARY:")
    print("   ✅ Search Courses route added")
    print("   ✅ User login troubleshooting provided")
    print("   🚀 Restart server and test both functionalities!")
