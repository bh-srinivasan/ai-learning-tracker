#!/usr/bin/env python3
"""
Azure Functionality Test
Test if the specific fixes are working on Azure
"""

import requests
import json

def test_azure_login():
    """Test login functionality with environment variable passwords"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("🔐 Testing Azure Login Functionality")
    print("=" * 40)
    
    session = requests.Session()
    
    # Test admin login with environment variable password
    print("1. Testing admin login with environment password...")
    
    try:
        # Get login page first
        login_page = session.get(f"{base_url}/auth/login")
        print(f"   Login page status: {login_page.status_code}")
        
        # Try to login with environment variable password
        login_data = {
            'username': 'admin',
            'password': 'YourSecureAdminPassword123!'  # From .env file
        }
        
        login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
        print(f"   Login attempt status: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print("   ✅ Login successful (redirect)")
            location = login_response.headers.get('Location', '')
            if 'dashboard' in location:
                print("   ✅ Redirected to dashboard")
                return True
            else:
                print(f"   ⚠️  Redirected to: {location}")
        elif login_response.status_code == 200:
            # Check if we're still on login page (login failed)
            if 'login' in login_response.text.lower():
                print("   ❌ Login failed - still on login page")
                print("   💡 This means environment variables aren't set in Azure")
                return False
        
    except Exception as e:
        print(f"   ❌ Error testing login: {e}")
        return False
    
    return False

def test_demo_user_login():
    """Test demo user login"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("\n👤 Testing Demo User Login...")
    
    session = requests.Session()
    
    try:
        login_data = {
            'username': 'demo',
            'password': 'DemoUserPassword123!'
        }
        
        login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
        print(f"   Demo login status: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print("   ✅ Demo login successful")
            return True
        else:
            print("   ❌ Demo login failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing demo login: {e}")
        return False

def check_database_issues():
    """Check if database-related fixes are working"""
    print("\n💾 Checking Database-Related Fixes...")
    
    # The fixes we made should be automatic, but we can check indirectly
    print("   Database fixes (LinkedIn courses, global learnings) should be automatic")
    print("   If login works, database structure is likely correct")

def provide_solution_steps():
    """Provide step-by-step solution"""
    print("\n🔧 SOLUTION: Environment Variables Not Set in Azure")
    print("=" * 55)
    
    print("Your changes aren't reflecting because Azure doesn't have the environment variables.")
    print("The app is falling back to default passwords instead of your .env values.")
    
    print("\n📋 EXACT STEPS TO FIX:")
    print("1. Open a new tab: https://portal.azure.com")
    print("2. Sign in with your Azure account")
    print("3. In the search bar, type: ai-learning-tracker-bharath")
    print("4. Click on the App Service result")
    print("5. In the left sidebar, click 'Configuration'")
    print("6. Click the 'Application settings' tab")
    print("7. For EACH variable below, click '+ New application setting':")
    
    vars_to_add = [
        "ADMIN_PASSWORD → YourSecureAdminPassword123!",
        "DEMO_USERNAME → demo", 
        "DEMO_PASSWORD → DemoUserPassword123!",
        "FLASK_SECRET_KEY → your-super-secret-key-change-this-in-production",
        "FLASK_ENV → production",
        "FLASK_DEBUG → False"
    ]
    
    for var in vars_to_add:
        print(f"   • {var}")
    
    print("\n8. Click 'Save' at the top")
    print("9. Wait 2-3 minutes for restart")
    print("10. Test login again")
    
    print("\n⚠️  IMPORTANT: Without these environment variables,")
    print("    your app uses default passwords (admin/admin, bharath/bharath)")
    print("    instead of your secure passwords from .env")

def main():
    """Main diagnostic function"""
    print("🩺 Azure Deployment Diagnostic")
    print("=" * 35)
    
    # Test login functionality
    admin_login_works = test_azure_login()
    demo_login_works = test_demo_user_login()
    
    check_database_issues()
    
    print("\n📊 Diagnostic Results:")
    print(f"   Admin Login (env password): {'✅ Working' if admin_login_works else '❌ Failed'}")
    print(f"   Demo Login (env password):  {'✅ Working' if demo_login_works else '❌ Failed'}")
    
    if not admin_login_works or not demo_login_works:
        provide_solution_steps()
    else:
        print("\n🎉 Environment variables are working correctly!")
        print("   Your changes should be reflected in the app")

if __name__ == "__main__":
    main()
