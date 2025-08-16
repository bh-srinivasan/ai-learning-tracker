#!/usr/bin/env python3
"""
Test Azure App After Fix
Verify that the 500 error has been resolved
"""

import requests
import time
from datetime import datetime

def test_azure_app():
    """Test the Azure app to see if the 500 error is fixed"""
    print("🧪 Testing Azure App After Fix")
    print("=" * 40)
    print(f"Timestamp: {datetime.now()}")
    
    app_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print(f"\n🌐 Testing: {app_url}")
    print("Waiting for Azure deployment to complete...")
    
    # Give Azure a moment to restart after deployment
    time.sleep(10)
    
    try:
        # Test the main page
        print("\n📋 Testing main page...")
        response = requests.get(app_url, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Application is now working!")
            print(f"Content preview: {response.text[:200]}...")
            
            # Test a few more endpoints
            test_endpoints = [
                "/login",
                "/dashboard", 
                "/admin"
            ]
            
            print("\n🔍 Testing additional endpoints:")
            for endpoint in test_endpoints:
                try:
                    test_response = requests.get(f"{app_url}{endpoint}", timeout=30)
                    status = "✅" if test_response.status_code in [200, 302, 401, 403] else "❌"
                    print(f"  {status} {endpoint}: {test_response.status_code}")
                except Exception as e:
                    print(f"  ❌ {endpoint}: Error - {e}")
            
            return True
            
        elif response.status_code == 500:
            print("❌ Still getting 500 Internal Server Error")
            print(f"Response content: {response.text[:500]}")
            return False
            
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - app may still be starting up")
        print("💡 Try again in a few minutes")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run the test"""
    success = test_azure_app()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 AZURE FIX SUCCESSFUL!")
        print("The 500 Internal Server Error has been resolved.")
        print("Your application is now running properly on Azure!")
    else:
        print("❌ ISSUE REMAINS")
        print("The application is still experiencing issues.")
        print("Check Azure App Service logs for more details.")
    
    print("\n💡 Next steps:")
    if success:
        print("- Test all application features")
        print("- Monitor Azure logs for any warnings")
        print("- Set up proper monitoring and alerts")
    else:
        print("- Check Azure App Service logs in the portal")
        print("- Verify startup command configuration")
        print("- Check environment variables in Azure")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
