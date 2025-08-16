"""
Azure Environment Check Script
Run this to check what environment variables are set in Azure App Service
"""

import requests
import json

def check_azure_environment():
    """Check Azure environment variables via the debug endpoint"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("=" * 60)
    print("CHECKING AZURE ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    try:
        # Check the debug endpoint
        response = requests.get(f"{base_url}/debug/env", timeout=30)
        
        if response.status_code == 200:
            env_data = response.json()
            print("✅ Successfully retrieved environment data:")
            print("-" * 40)
            for key, value in env_data.items():
                print(f"{key:25}: {value}")
            
            # Check if critical variables are set
            critical_missing = []
            if env_data.get('azure_sql_password_set') == 'no':
                critical_missing.append('AZURE_SQL_PASSWORD')
            if env_data.get('admin_password_set') == 'no':
                critical_missing.append('ADMIN_PASSWORD')
            
            if critical_missing:
                print(f"\n⚠️  CRITICAL: Missing environment variables: {critical_missing}")
                print("These need to be set in Azure App Service > Configuration > Application settings")
            else:
                print("\n✅ All critical environment variables are set")
                
        elif response.status_code == 403:
            print("❌ Access denied - need admin session to access debug endpoint")
            print("Try logging in as admin first")
        else:
            print(f"❌ Failed to get environment data: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the Azure app is running")

def test_admin_login():
    """Test admin login with current settings"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("\n" + "=" * 60)
    print("TESTING ADMIN LOGIN")
    print("=" * 60)
    
    # Test passwords to try
    passwords_to_try = [
        "AILearning2025!",  # Original hardcoded
        "YourSecureAdminPassword123!",  # From .env
        "DefaultSecurePassword123!"  # Fallback default
    ]
    
    session = requests.Session()
    
    for password in passwords_to_try:
        print(f"\n🔐 Testing password: {'*' * len(password)}")
        
        try:
            # Get login page first for CSRF token if needed
            login_page = session.get(f"{base_url}/admin/login", timeout=30)
            
            # Attempt login
            login_data = {
                'username': 'admin',
                'password': password
            }
            
            response = session.post(f"{base_url}/admin/login", 
                                  data=login_data, 
                                  timeout=30,
                                  allow_redirects=False)
            
            if response.status_code == 302:
                print(f"✅ Login successful with this password!")
                
                # Check where it redirects
                redirect_location = response.headers.get('Location', '')
                print(f"   Redirects to: {redirect_location}")
                
                # Try to access admin dashboard
                dashboard_response = session.get(f"{base_url}/admin/dashboard", timeout=30)
                if dashboard_response.status_code == 200:
                    print("✅ Admin dashboard accessible")
                    return True
                else:
                    print(f"❌ Admin dashboard error: {dashboard_response.status_code}")
                    
            elif response.status_code == 200:
                print("❌ Login form returned (likely failed)")
                if 'Invalid credentials' in response.text:
                    print("   Error: Invalid credentials")
                elif 'error' in response.text.lower():
                    print("   Error found in response")
                    
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    return False

if __name__ == "__main__":
    check_azure_environment()
    
    # Test admin login
    login_success = test_admin_login()
    
    if not login_success:
        print("\n🔧 TROUBLESHOOTING RECOMMENDATIONS:")
        print("1. Check Azure App Service > Configuration > Application settings")
        print("2. Ensure ADMIN_PASSWORD is set to the correct value")
        print("3. Ensure AZURE_SQL_PASSWORD is set for database connection")
        print("4. Check application logs in Azure portal")
        print("5. Restart the Azure App Service if environment variables were just added")
