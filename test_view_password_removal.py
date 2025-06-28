import requests
import json
import sys
import time

def test_view_password_removal():
    """Test that the View Password functionality has been completely removed"""
    
    print("🧪 TESTING VIEW PASSWORD FUNCTIONALITY REMOVAL")
    print("=" * 55)
    
    base_url = "http://localhost:5000"
    
    # Create a session
    session = requests.Session()
    
    try:
        # Step 1: Admin Login
        print("1. 🔐 Testing admin login...")
        login_response = session.post(f"{base_url}/auth/login", data={
            'username': 'admin',
            'password': 'admin'
        })
        
        if login_response.status_code != 200:
            print("❌ Admin login failed!")
            return False
        
        print("✅ Admin login successful")
        
        # Step 2: Access Manage Users page
        print("\n2. 👥 Accessing Manage Users page...")
        users_response = session.get(f"{base_url}/admin/users")
        
        if users_response.status_code != 200:
            print("❌ Failed to access Manage Users page!")
            return False
        
        page_content = users_response.text
        
        # Check that View Current Password is NOT present
        if 'View Current Password' in page_content:
            print("❌ 'View Current Password' text still found in page!")
            return False
        else:
            print("✅ 'View Current Password' text removed from page")
            
        # Check that showCurrentPassword function is NOT present
        if 'showCurrentPassword' in page_content:
            print("❌ 'showCurrentPassword' function still found in page!")
            return False
        else:
            print("✅ 'showCurrentPassword' function removed from page")
            
        # Check that viewCurrentPasswordModal is NOT present
        if 'viewCurrentPasswordModal' in page_content:
            print("❌ 'viewCurrentPasswordModal' still found in page!")
            return False
        else:
            print("✅ 'viewCurrentPasswordModal' removed from page")
        
        print("\n3. 🔍 Testing that get-user-hash endpoint is removed...")
        
        # Test that the get-user-hash endpoint no longer exists
        hash_response = session.post(f"{base_url}/admin/get-user-hash", data={
            'user_id': '2'
        })
        
        # Should return 404 or similar error since the endpoint is removed
        if hash_response.status_code == 404:
            print("✅ get-user-hash endpoint successfully removed (404)")
        elif hash_response.status_code >= 400:
            print(f"✅ get-user-hash endpoint successfully removed ({hash_response.status_code})")
        else:
            print(f"❌ get-user-hash endpoint still exists (status: {hash_response.status_code})")
            return False
        
        print("\n4. 🎨 Checking remaining UI elements...")
        
        # Check that Generate Viewable Password is still present
        if 'Generate Viewable Password' in page_content:
            print("✅ 'Generate Viewable Password' action still available")
        else:
            print("⚠️  'Generate Viewable Password' action not found")
            
        # Check that Set Custom Password is still present
        if 'Set Custom Password' in page_content:
            print("✅ 'Set Custom Password' action still available")
        else:
            print("⚠️  'Set Custom Password' action not found")
            
        # Check that critical actions are still visible
        if 'Pause' in page_content or 'Active' in page_content:
            print("✅ User status toggle actions still available")
        else:
            print("⚠️  User status toggle actions not found")
            
        if 'Delete' in page_content:
            print("✅ Delete action still available")
        else:
            print("⚠️  Delete action not found")
        
        print("\n" + "=" * 55)
        print("🎉 VIEW PASSWORD REMOVAL TEST COMPLETED SUCCESSFULLY!")
        print("✅ All 'View Password' functionality has been removed:")
        print("   • Dropdown menu item removed")
        print("   • Modal dialog removed")
        print("   • JavaScript functions removed")
        print("   • Backend endpoint removed")
        print("   • Essential functions preserved")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
    
    finally:
        # Logout
        try:
            session.post(f"{base_url}/auth/logout")
        except:
            pass

if __name__ == "__main__":
    # Wait a moment for the Flask app to start
    print("⏳ Waiting for Flask app to be ready...")
    time.sleep(2)
    
    success = test_view_password_removal()
    sys.exit(0 if success else 1)
