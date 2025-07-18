#!/usr/bin/env python3
"""
Direct Azure Database Admin Initializer
=======================================

Creates admin user directly by understanding Azure database structure.
Safe approach that works regardless of app routing.
"""

import requests
import os
import json
import time

def check_and_create_admin():
    """Check if admin can login, create if not"""
    
    print("=== DIRECT AZURE ADMIN CREATION ===")
    
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    print(f"🔍 Testing admin login to determine database state...")
    print(f"   URL: {base_url}")
    print(f"   Username: admin")
    print(f"   Password: {'*' * len(admin_password)}")
    
    try:
        session = requests.Session()
        
        # Test admin login
        response = session.get(base_url)
        if response.status_code != 200:
            print(f"❌ App not responding: {response.status_code}")
            return False
        
        # Try to login
        login_data = {
            'username': 'admin',
            'password': admin_password
        }
        
        response = session.post(base_url, data=login_data, allow_redirects=False)
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/dashboard' in location:
                print("✅ ADMIN USER ALREADY EXISTS AND WORKS!")
                print("🎉 No initialization needed")
                return True
            elif '/login' in location or location == '/':
                print("❌ Admin login failed - admin user likely missing")
                print("🔧 Need to create admin user")
                return False
        
        print(f"⚠️ Unexpected response: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return False

def try_create_via_signup():
    """Try to create admin via signup if available"""
    
    print("\n=== ATTEMPTING ADMIN CREATION VIA SIGNUP ===")
    
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    try:
        session = requests.Session()
        
        # Check if there's a signup route
        signup_urls = ['/signup', '/register', '/create-user']
        
        for signup_path in signup_urls:
            try:
                signup_url = f"{base_url}{signup_path}"
                response = session.get(signup_url)
                
                if response.status_code == 200 and 'signup' in response.text.lower():
                    print(f"✅ Found signup form at: {signup_path}")
                    
                    # Try to register admin
                    signup_data = {
                        'username': 'admin',
                        'password': admin_password,
                        'level': 'Advanced'
                    }
                    
                    response = session.post(signup_url, data=signup_data)
                    
                    if response.status_code == 302 or 'success' in response.text.lower():
                        print("✅ Admin user created via signup!")
                        return True
                        
            except Exception:
                continue
        
        print("❌ No accessible signup routes found")
        return False
        
    except Exception as e:
        print(f"❌ Error with signup approach: {e}")
        return False

def manual_database_instructions():
    """Provide manual database setup instructions"""
    
    print("\n=== MANUAL DATABASE SETUP INSTRUCTIONS ===")
    print()
    print("Since automatic creation isn't working, here are manual options:")
    print()
    print("🔧 OPTION 1: Azure CLI Database Access")
    print("   1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
    print("   2. Login: az login")
    print("   3. Connect to app: az webapp ssh --resource-group rg-ai-learning-tracker --name ai-learning-tracker-bharath")
    print("   4. Run: cd /home/site/wwwroot && python initialize_azure_admin.py")
    print()
    print("🔧 OPTION 2: Azure Portal Console")
    print("   1. Go to Azure Portal")
    print("   2. Find your App Service: ai-learning-tracker-bharath")
    print("   3. Go to Development Tools > Console")
    print("   4. Run: python initialize_azure_admin.py")
    print()
    print("🔧 OPTION 3: Re-deployment with Auto-Init")
    print("   1. The pipeline should run initialization automatically")
    print("   2. Check Azure DevOps logs for any initialization errors")
    print("   3. Environment variables (ADMIN_PASSWORD) must be set in Azure")
    print()
    print("📋 VERIFICATION:")
    print("   After setup, test login at:")
    print(f"   URL: https://ai-learning-tracker-bharath.azurewebsites.net/")
    print("   Username: admin")
    print("   Password: [your ADMIN_PASSWORD]")

def main():
    """Main function"""
    
    print("AI Learning Tracker - Direct Azure Admin Creator")
    print("=" * 60)
    
    # Check current state
    admin_exists = check_and_create_admin()
    
    if admin_exists:
        print("\n🎉 SUCCESS! Admin user is working!")
        print("✅ Your Azure deployment is ready to use")
        return True
    
    # Try signup approach
    signup_success = try_create_via_signup()
    
    if signup_success:
        # Test login again
        print("\n🔍 Testing admin login after signup...")
        admin_works = check_and_create_admin()
        
        if admin_works:
            print("\n🎉 SUCCESS! Admin created and working!")
            return True
    
    # Provide manual instructions
    manual_database_instructions()
    
    print("\n" + "=" * 60)
    print("⚠️ AUTOMATIC CREATION FAILED")
    print("🔧 Please use the manual options above")
    print("💡 Most likely the Azure database is empty and needs initialization")
    
    return False

if __name__ == "__main__":
    main()
