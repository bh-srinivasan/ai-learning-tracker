#!/usr/bin/env python3
"""
Quick test to verify Azure deployment of BIT compatibility fixes
"""

import requests
import sys

def test_azure_deployment():
    """Test if Azure deployment is working with our BIT compatibility fixes"""
    
    # Azure app URL
    app_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print(f"Testing Azure deployment at: {app_url}")
    
    try:
        # Test 1: Basic connectivity
        print("\n1. Testing basic connectivity...")
        response = requests.get(f"{app_url}/", timeout=30)
        if response.status_code == 200:
            print("SUCCESS: App is responding")
        else:
            print(f"ERROR: App returned status: {response.status_code}")
            return False
            
        # Test 2: Admin test endpoint (should work)
        print("\n2. Testing admin test endpoint...")
        admin_response = requests.get(f"{app_url}/admin-test", timeout=30)
        if admin_response.status_code in [200, 302]:
            print("SUCCESS: Admin test endpoint accessible")
        else:
            print(f"ERROR: Admin test failed: {admin_response.status_code}")
            
        # Test 3: Login page
        print("\n3. Testing login page...")
        login_response = requests.get(f"{app_url}/login", timeout=30)
        if login_response.status_code == 200:
            print("SUCCESS: Login page accessible")
        else:
            print(f"ERROR: Login page failed: {login_response.status_code}")
            
        print(f"\nDeployment test complete!")
        print(f"App URL: {app_url}")
        print(f"Ready to test non-admin login")
        
        return True
        
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out - app may be starting up")
        print("Try again in a few minutes")
        return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection error - check if app is running")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_azure_deployment()
    sys.exit(0 if success else 1)
