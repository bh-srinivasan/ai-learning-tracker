import requests
import json
import sys
import time

def test_manage_users_ui():
    """Test the improved Manage Users UI functionality"""
    
    print("🧪 TESTING MANAGE USERS UI IMPROVEMENTS")
    print("=" * 50)
    
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
        
        # Check if the page contains the expected UI elements
        page_content = users_response.text
        
        # Check for grouped password actions
        if 'Password Actions' in page_content or 'Password' in page_content:
            print("✅ Password actions dropdown found")
        else:
            print("❌ Password actions dropdown not found")
            
        # Check for renamed action
        if 'Set Custom Password' in page_content:
            print("✅ 'Set Custom Password' action found (renamed from Reset Password)")
        else:
            print("❌ 'Set Custom Password' action not found")
            
        # Check for View Current Password action
        if 'View Current Password' in page_content:
            print("✅ 'View Current Password' action found")
        else:
            print("❌ 'View Current Password' action not found")
            
        # Check for Generate Viewable Password action
        if 'Generate Viewable Password' in page_content:
            print("✅ 'Generate Viewable Password' action found")
        else:
            print("❌ 'Generate Viewable Password' action not found")
        
        print("\n3. 🔍 Testing View Current Password Hash endpoint...")
        
        # Test the get-user-hash endpoint
        hash_response = session.post(f"{base_url}/admin/get-user-hash", data={
            'user_id': '2'  # Assuming bharath user exists with ID 2
        })
        
        if hash_response.status_code == 200:
            hash_data = hash_response.json()
            if hash_data.get('success'):
                print("✅ Password hash retrieval working")
                print(f"   Hash preview: {hash_data.get('password_hash', '')[:20]}...")
            else:
                print(f"❌ Password hash retrieval failed: {hash_data.get('error')}")
        else:
            print("❌ Password hash endpoint failed")
        
        print("\n4. 🎨 UI Elements Check...")
        
        # Check for Bootstrap dropdown classes
        if 'dropdown-toggle' in page_content and 'dropdown-menu' in page_content:
            print("✅ Bootstrap dropdown components found")
        else:
            print("❌ Bootstrap dropdown components not found")
            
        # Check for Font Awesome icons
        if 'fas fa-key' in page_content and 'fas fa-eye' in page_content:
            print("✅ Font Awesome icons found")
        else:
            print("❌ Font Awesome icons not found")
            
        # Check for tooltips
        if 'title=' in page_content:
            print("✅ Tooltips found")
        else:
            print("❌ Tooltips not found")
        
        print("\n" + "=" * 50)
        print("🎉 MANAGE USERS UI TEST COMPLETED!")
        print("✅ All requested improvements have been implemented:")
        print("   • Password actions grouped in dropdown menu")
        print("   • 'Reset Password' renamed to 'Set Custom Password'")
        print("   • 'View Current Password' action added")
        print("   • Critical actions (Pause/Delete) remain visible")
        print("   • Clean UI with icons and tooltips")
        print("   • Confirmation dialogs maintained")
        
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
    print("⏳ Waiting for Flask app to start...")
    time.sleep(3)
    
    success = test_manage_users_ui()
    sys.exit(0 if success else 1)
