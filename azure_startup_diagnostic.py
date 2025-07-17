#!/usr/bin/env python3
"""
Simple Azure Startup Diagnostic Tool
"""
import requests
import time
import json

def test_azure_startup():
    """Test Azure app startup and basic functionality"""
    url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("🔧 AZURE STARTUP DIAGNOSTIC")
    print("=" * 40)
    
    # Test 1: Basic connectivity with longer timeout
    print("\n1️⃣ Testing basic connectivity...")
    try:
        response = requests.get(url, timeout=60)
        print(f"   Status: {response.status_code}")
        print(f"   Content Length: {len(response.content)}")
        if response.status_code == 200:
            print("   ✅ Basic connectivity: SUCCESS")
        else:
            print(f"   ❌ Bad status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout after 60 seconds")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
        return False
    
    # Test 2: Check response content for errors
    print("\n2️⃣ Analyzing response content...")
    content = response.text.lower()
    
    error_indicators = [
        'application error',
        'internal server error',
        'service unavailable',
        'python error',
        'traceback',
        'import error',
        'module not found'
    ]
    
    errors_found = []
    for indicator in error_indicators:
        if indicator in content:
            errors_found.append(indicator)
    
    if errors_found:
        print(f"   ❌ Error indicators found: {', '.join(errors_found)}")
        print(f"   Content preview: {response.text[:500]}...")
        return False
    else:
        print("   ✅ No error indicators found")
    
    # Test 3: Check if it's actually our Flask app
    print("\n3️⃣ Verifying Flask application...")
    if 'ai learning tracker' in content:
        print("   ✅ Correct Flask app detected")
    else:
        print("   ❌ Not our Flask app")
        return False
    
    # Test 4: Test login endpoint
    print("\n4️⃣ Testing login endpoint...")
    try:
        login_response = requests.get(f"{url}/auth/login", timeout=30)
        if login_response.status_code == 200:
            print("   ✅ Login endpoint working")
        else:
            print(f"   ❌ Login endpoint status: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Login endpoint error: {str(e)}")
        return False
    
    print("\n🎉 AZURE APP IS WORKING CORRECTLY!")
    print("✅ All diagnostic tests passed")
    return True

if __name__ == "__main__":
    success = test_azure_startup()
    exit(0 if success else 1)
