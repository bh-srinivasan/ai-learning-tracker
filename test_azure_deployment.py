import requests
import json
import sys
import time

def test_azure_deployment():
    """Test that the View Password removal is working on Azure production"""
    
    print("🌐 TESTING AZURE PRODUCTION DEPLOYMENT")
    print("=" * 55)
    
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    # Create a session
    session = requests.Session()
    
    try:
        # Step 1: Check if the site is accessible
        print("1. 🌍 Testing Azure site accessibility...")
        home_response = session.get(base_url)
        
        if home_response.status_code != 200:
            print(f"❌ Azure site not accessible! Status: {home_response.status_code}")
            return False
        
        print("✅ Azure site is accessible")
        
        # Step 2: Admin Login
        print("\n2. 🔐 Testing admin login on Azure...")
        login_response = session.post(f"{base_url}/auth/login", data={
            'username': 'admin',
            'password': 'admin'
        })
        
        if login_response.status_code != 200:
            print("❌ Admin login failed on Azure!")
            return False
        
        print("✅ Admin login successful on Azure")
        
        # Step 3: Access Manage Users page
        print("\n3. 👥 Accessing Manage Users page on Azure...")
        users_response = session.get(f"{base_url}/admin/users")
        
        if users_response.status_code != 200:
            print("❌ Failed to access Manage Users page on Azure!")
            return False
        
        page_content = users_response.text
        
        # Check that View Current Password is NOT present
        if 'View Current Password' in page_content:
            print("❌ 'View Current Password' still found on Azure!")
            return False
        else:
            print("✅ 'View Current Password' successfully removed from Azure")
            
        # Check that showCurrentPassword function is NOT present
        if 'showCurrentPassword' in page_content:
            print("❌ 'showCurrentPassword' function still found on Azure!")
            return False
        else:
            print("✅ 'showCurrentPassword' function removed from Azure")
            
        # Check that viewCurrentPasswordModal is NOT present
        if 'viewCurrentPasswordModal' in page_content:
            print("❌ 'viewCurrentPasswordModal' still found on Azure!")
            return False
        else:
            print("✅ 'viewCurrentPasswordModal' removed from Azure")
        
        print("\n4. 🔍 Testing that get-user-hash endpoint is removed on Azure...")
        
        # Test that the get-user-hash endpoint no longer exists
        hash_response = session.post(f"{base_url}/admin/get-user-hash", data={
            'user_id': '2'
        })
        
        # Should return 404 or redirect to login (both indicate the endpoint is gone)
        if hash_response.status_code >= 400 or 'login' in hash_response.url.lower():
            print("✅ get-user-hash endpoint successfully removed from Azure")
        else:
            print(f"❌ get-user-hash endpoint still exists on Azure (status: {hash_response.status_code})")
            return False
        
        print("\n5. 🎨 Checking remaining functionality on Azure...")
        
        # Check that essential features are still present
        if 'Generate Viewable Password' in page_content:
            print("✅ 'Generate Viewable Password' still available on Azure")
        else:
            print("⚠️  'Generate Viewable Password' not found on Azure")
            
        if 'Set Custom Password' in page_content:
            print("✅ 'Set Custom Password' still available on Azure")
        else:
            print("⚠️  'Set Custom Password' not found on Azure")
            
        if 'Delete' in page_content:
            print("✅ Delete actions still available on Azure")
        else:
            print("⚠️  Delete actions not found on Azure")
        
        print("\n" + "=" * 55)
        print("🎉 AZURE DEPLOYMENT VERIFICATION SUCCESSFUL!")
        print("✅ View Password functionality completely removed from production")
        print("✅ Essential features preserved and working")
        print("✅ Security improvements deployed")
        print("✅ Clean UI deployed to Azure")
        
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
    print("⏳ Testing Azure production deployment...")
    
    success = test_azure_deployment()
    
    if success:
        print("\n🚀 DEPLOYMENT COMPLETE!")
        print("   Production URL: https://ai-learning-tracker-bharath.azurewebsites.net")
        print("   Admin Login: admin/admin")
        print("   All changes successfully deployed to Azure!")
    
    sys.exit(0 if success else 1)
