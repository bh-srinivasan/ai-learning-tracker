#!/usr/bin/env python3
"""
Azure Environment Variables Checker
Check if Azure has the required environment variables configured
"""

import requests
import json

def check_azure_app_status():
    """Check if the Azure app is running and what might be missing"""
    app_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("🔍 Checking Azure App Status and Environment Variables")
    print("=" * 60)
    
    try:
        print("1. Testing app accessibility...")
        response = requests.get(app_url, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ Server Error (500) - Likely missing environment variables!")
            print("💡 This usually means environment variables aren't set in Azure")
            
        elif response.status_code == 200:
            print("✅ App is responding")
            
            # Check if we get login page or error page
            content = response.text.lower()
            if "error" in content:
                print("⚠️  App loaded but may have configuration errors")
            elif "login" in content:
                print("✅ Login page loaded successfully")
            else:
                print("ℹ️  App loaded with different content")
                
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - app might be starting up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🌐 App URL: {app_url}")

def provide_azure_config_instructions():
    """Provide step-by-step Azure configuration instructions"""
    print("\n🔧 Azure Environment Variables Setup")
    print("=" * 40)
    
    print("The issue is likely that environment variables aren't set in Azure.")
    print("Here's exactly how to fix it:")
    
    print("\n📋 Step-by-Step Instructions:")
    print("1. Go to https://portal.azure.com")
    print("2. Search for 'ai-learning-tracker-bharath' or go to App Services")
    print("3. Click on your app service")
    print("4. In the left menu, click 'Configuration'")
    print("5. Click 'Application settings' tab")
    print("6. Click '+ New application setting' for each of these:")
    
    env_vars = [
        ("ADMIN_PASSWORD", "YourSecureAdminPassword123!"),
        ("DEMO_USERNAME", "demo"),
        ("DEMO_PASSWORD", "DemoUserPassword123!"),
        ("FLASK_SECRET_KEY", "your-super-secret-key-change-this-in-production"),
        ("FLASK_ENV", "production"),
        ("FLASK_DEBUG", "False"),
        ("SESSION_TIMEOUT", "3600"),
        ("PASSWORD_MIN_LENGTH", "8")
    ]
    
    print("\n🔑 Environment Variables to Add:")
    for name, value in env_vars:
        print(f"   Name: {name}")
        print(f"   Value: {value}")
        print("   ---")
    
    print("\n7. After adding all variables, click 'Save'")
    print("8. Wait for the app to restart (1-2 minutes)")
    print("9. Test the app again")

def test_specific_endpoints():
    """Test specific endpoints to diagnose issues"""
    app_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("\n🧪 Testing Specific Endpoints")
    print("=" * 35)
    
    endpoints = [
        "/",
        "/auth/login",
        "/dashboard"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{app_url}{endpoint}"
            response = requests.get(url, timeout=15)
            print(f"   {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")

if __name__ == "__main__":
    check_azure_app_status()
    provide_azure_config_instructions()
    test_specific_endpoints()
    
    print("\n💡 Quick Diagnosis:")
    print("   - If you see 500 errors: Environment variables missing")
    print("   - If you see 404 errors: Routing issues")
    print("   - If you see timeouts: App might be sleeping")
    print("   - If you see 200: App is working, check functionality")
