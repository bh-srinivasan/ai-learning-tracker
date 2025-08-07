#!/usr/bin/env python3
"""
Azure Deployment Environment Checker
Checks environment variables in the actual Azure deployment
"""

import requests
import json
import sys
from datetime import datetime

class AzureEnvironmentChecker:
    def __init__(self, azure_url="https://ai-learning-tracker-bharath.azurewebsites.net"):
        self.azure_url = azure_url
        self.required_vars = [
            'azure_sql_server',
            'azure_sql_database', 
            'azure_sql_username',
            'azure_sql_password_set',
            'admin_password_set'
        ]

    def check_azure_environment(self):
        """Check environment variables in Azure deployment"""
        print("=" * 70)
        print("AZURE DEPLOYMENT ENVIRONMENT CHECK")
        print("=" * 70)
        print(f"Checking: {self.azure_url}")
        print(f"Timestamp: {datetime.now()}")
        print()
        
        try:
            # Check the debug endpoint
            response = requests.get(f"{self.azure_url}/debug/env", timeout=30)
            
            if response.status_code == 200:
                env_data = response.json()
                
                print("✅ Successfully connected to Azure deployment")
                print("-" * 50)
                
                # Check if this is actually Azure environment
                if env_data.get('is_azure_env') == 'SET':
                    print("✅ Confirmed: Running in Azure App Service")
                else:
                    print("⚠️  Warning: May not be running in Azure App Service")
                
                print()
                print("ENVIRONMENT VARIABLES STATUS:")
                print("-" * 50)
                
                all_set = True
                missing_vars = []
                
                for key, value in env_data.items():
                    if key in ['azure_sql_password_set', 'admin_password_set']:
                        if value == 'SET':
                            print(f"✅ {key:25}: {value}")
                        else:
                            print(f"❌ {key:25}: {value}")
                            all_set = False
                            missing_vars.append(key)
                    elif key in ['azure_sql_server', 'azure_sql_database', 'azure_sql_username']:
                        if value == 'SET':
                            print(f"✅ {key:25}: {value}")
                        else:
                            print(f"❌ {key:25}: {value}")
                            all_set = False
                            missing_vars.append(key)
                    else:
                        print(f"ℹ️  {key:25}: {value}")
                
                print()
                print("DIAGNOSIS:")
                print("-" * 50)
                
                if all_set:
                    print("✅ All required environment variables are set in Azure")
                    print("✅ Database connection should work")
                    
                    # Test admin routes
                    self.test_admin_routes()
                else:
                    print(f"❌ Missing environment variables: {missing_vars}")
                    print("\n🔧 SOLUTION:")
                    print("1. Go to Azure Portal")
                    print("2. Navigate to: App Services > ai-learning-tracker-bharath > Configuration")
                    print("3. Under 'Application settings', add these missing variables:")
                    
                    for var in missing_vars:
                        if 'password' in var:
                            print(f"   - {var.upper().replace('_SET', '')}: [Your secure password]")
                        elif 'server' in var:
                            print(f"   - {var.upper()}: ai-learning-sql-centralus.database.windows.net")
                        elif 'database' in var:
                            print(f"   - {var.upper()}: ai-learning-db")
                        elif 'username' in var:
                            print(f"   - {var.upper()}: ailearningadmin")
                    
                    print("4. Click 'Save'")
                    print("5. Restart the App Service")
                
                return env_data, all_set
                    
            else:
                print(f"❌ Failed to connect to Azure debug endpoint: {response.status_code}")
                print(f"Response: {response.text}")
                return None, False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            print("Make sure the Azure app is running and accessible")
            return None, False

    def test_admin_routes(self):
        """Test if admin routes are available"""
        print("\nTESTING ADMIN ROUTES:")
        print("-" * 50)
        
        admin_routes = [
            '/admin/login',
            '/admin/dashboard', 
            '/admin/test-login'
        ]
        
        for route in admin_routes:
            try:
                response = requests.get(f"{self.azure_url}{route}", timeout=10, allow_redirects=False)
                
                if response.status_code == 200:
                    print(f"✅ {route:20}: Available")
                elif response.status_code == 302:
                    print(f"🔄 {route:20}: Redirects (likely requires login)")
                elif response.status_code == 404:
                    print(f"❌ {route:20}: Not Found")
                else:
                    print(f"⚠️  {route:20}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {route:20}: Error - {e}")

    def test_database_connection(self):
        """Test if database connection works by checking a simple endpoint"""
        print("\nTESTING DATABASE CONNECTION:")
        print("-" * 50)
        
        # Try to access a route that would require database access
        try:
            response = requests.get(f"{self.azure_url}/", timeout=10)
            if response.status_code == 200:
                print("✅ Main page loads (basic app functionality works)")
                
                # Check if we can reach login (which requires some DB access)
                login_response = requests.get(f"{self.azure_url}/login", timeout=10)
                if login_response.status_code == 200:
                    print("✅ Login page loads (database likely accessible)")
                else:
                    print(f"⚠️  Login page error: {login_response.status_code}")
            else:
                print(f"❌ Main page error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")

def main():
    """Main function"""
    checker = AzureEnvironmentChecker()
    
    try:
        env_data, all_valid = checker.check_azure_environment()
        
        if env_data:
            checker.test_database_connection()
        
        if not all_valid:
            print("\n" + "="*70)
            print("SUMMARY: Environment variables need to be configured in Azure")
            print("="*70)
            sys.exit(1)
        else:
            print("\n" + "="*70)
            print("SUMMARY: All environment variables are properly configured")
            print("="*70)
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error during check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
