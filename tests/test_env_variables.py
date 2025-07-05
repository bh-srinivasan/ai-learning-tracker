#!/usr/bin/env python3
"""
Environment Variables Verification Test
======================================

This script specifically tests if the environment variables you set in Azure
are actually being used by the application.
"""

import requests
import time
from urllib.parse import urljoin

class EnvironmentVariablesTest:
    def __init__(self):
        self.base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
        self.session = requests.Session()
        
    def test_new_admin_credentials(self):
        """Test if new admin password from environment variable works"""
        print("🔐 Testing NEW admin password from environment variables...")
        
        login_url = urljoin(self.base_url, "/auth/login")
        
        # Try the NEW password from your .env file
        new_credentials = {
            'username': 'admin',
            'password': 'YourSecureAdminPassword123!'
        }
        
        try:
            # Get login page
            response = self.session.get(login_url)
            if response.status_code != 200:
                print(f"❌ Could not access login page: {response.status_code}")
                return False
            
            # Try login with NEW credentials
            response = self.session.post(login_url, data=new_credentials, allow_redirects=False)
            
            if response.status_code == 302:  # Redirect on success
                print("✅ NEW admin password WORKS! Environment variables are active!")
                return True
            else:
                print("❌ NEW admin password FAILED. Environment variables may not be active yet.")
                return False
                
        except Exception as e:
            print(f"❌ Error testing new admin credentials: {e}")
            return False
    
    def test_old_admin_credentials(self):
        """Test if old admin password still works (fallback)"""
        print("🔐 Testing OLD admin password (fallback)...")
        
        login_url = urljoin(self.base_url, "/auth/login")
        
        # Try the OLD password (fallback)
        old_credentials = {
            'username': 'admin',
            'password': 'admin'
        }
        
        try:
            # Logout first
            logout_url = urljoin(self.base_url, "/auth/logout")
            self.session.get(logout_url)
            
            # Get login page
            response = self.session.get(login_url)
            if response.status_code != 200:
                print(f"❌ Could not access login page: {response.status_code}")
                return False
            
            # Try login with OLD credentials
            response = self.session.post(login_url, data=old_credentials, allow_redirects=False)
            
            if response.status_code == 302:  # Redirect on success
                print("⚠️  OLD admin password still works. Environment variables NOT active yet.")
                return True
            else:
                print("✅ OLD admin password REJECTED. Environment variables are working!")
                return False
                
        except Exception as e:
            print(f"❌ Error testing old admin credentials: {e}")
            return False
    
    def test_new_demo_credentials(self):
        """Test if new demo password works"""
        print("👤 Testing NEW demo password from environment variables...")
        
        login_url = urljoin(self.base_url, "/auth/login")
        
        # Try the NEW demo password from your .env file
        new_demo_credentials = {
            'username': 'demo',
            'password': 'DemoUserPassword123!'
        }
        
        try:
            # Logout first
            logout_url = urljoin(self.base_url, "/auth/logout")
            self.session.get(logout_url)
            
            # Get login page
            response = self.session.get(login_url)
            if response.status_code != 200:
                print(f"❌ Could not access login page: {response.status_code}")
                return False
            
            # Try login with NEW demo credentials
            response = self.session.post(login_url, data=new_demo_credentials, allow_redirects=False)
            
            if response.status_code == 302:  # Redirect on success
                print("✅ NEW demo password WORKS! Environment variables are active!")
                return True
            else:
                print("❌ NEW demo password FAILED. Environment variables may not be active yet.")
                return False
                
        except Exception as e:
            print(f"❌ Error testing new demo credentials: {e}")
            return False
    
    def check_azure_restart_status(self):
        """Check if Azure app needs restart after setting environment variables"""
        print("🔄 Checking if Azure app service needs restart...")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                print("✅ Azure app is responding")
                if "Environment variables may take a few minutes to activate" in response.text:
                    print("⏳ App indicates environment variables are still loading")
                return True
            else:
                print(f"⚠️  Azure app returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking Azure status: {e}")
            return False
    
    def run_environment_test(self):
        """Run comprehensive environment variables test"""
        print("🧪 ENVIRONMENT VARIABLES VERIFICATION TEST")
        print("=" * 55)
        print("Testing if your environment variables are active in Azure...\n")
        
        # Test site accessibility
        print("1. 🌍 Checking Azure site accessibility...")
        if not self.check_azure_restart_status():
            print("❌ Cannot proceed - Azure site not accessible")
            return
        
        # Test new credentials
        new_admin_works = self.test_new_admin_credentials()
        time.sleep(2)
        
        new_demo_works = self.test_new_demo_credentials()
        time.sleep(2)
        
        # Test old credentials (should fail if env vars are active)
        old_admin_works = self.test_old_admin_credentials()
        
        print("\n" + "=" * 55)
        print("📋 ENVIRONMENT VARIABLES TEST RESULTS:")
        print("-" * 40)
        
        if new_admin_works and new_demo_works and not old_admin_works:
            print("🎉 ENVIRONMENT VARIABLES ARE ACTIVE!")
            print("✅ New admin password works")
            print("✅ New demo password works") 
            print("✅ Old passwords rejected")
            print("\n🔑 Your new credentials are:")
            print("   Admin: admin / YourSecureAdminPassword123!")
            print("   Demo:  demo / DemoUserPassword123!")
            
        elif old_admin_works:
            print("⏳ ENVIRONMENT VARIABLES NOT ACTIVE YET")
            print("⚠️  Old passwords still working")
            print("💡 This is normal - Azure can take 2-10 minutes to restart")
            print("\n🔄 Next steps:")
            print("1. Wait 2-5 more minutes")
            print("2. Run this test again: python test_env_variables.py")
            print("3. If still not working, restart Azure app manually")
            
        else:
            print("❓ MIXED RESULTS - NEEDS INVESTIGATION")
            print("💡 Try manually restarting the Azure app service")
            
        print(f"\n🌐 Production URL: {self.base_url}")
        print("🔧 Azure Portal: https://portal.azure.com")

def main():
    tester = EnvironmentVariablesTest()
    tester.run_environment_test()

if __name__ == "__main__":
    main()
