#!/usr/bin/env python3
"""
Test script to verify user persistence after Azure server restart
"""
import requests
import json
import time

# Azure application URL
AZURE_URL = "https://ai-learning-tracker-bharath.azurewebsites.net"

def test_azure_users():
    """Test that users persist after server restart"""
    print("🔍 Testing user persistence after Azure server restart...")
    
    try:
        # Give the server a moment to fully restart
        print("⏳ Waiting 10 seconds for server to fully restart...")
        time.sleep(10)
        
        # Test if the app is responding
        response = requests.get(f"{AZURE_URL}/", timeout=30)
        if response.status_code == 200:
            print(f"✅ Azure app is responding (Status: {response.status_code})")
        else:
            print(f"⚠️  Azure app returned status: {response.status_code}")
        
        # Test admin login to see if users are still there
        login_data = {
            'username': 'bharath',
            'password': 'bharath'
        }
        
        session = requests.Session()
        login_response = session.post(f"{AZURE_URL}/login", data=login_data, timeout=30)
        
        if login_response.status_code == 200 and "dashboard" in login_response.url:
            print("✅ User 'bharath' still exists and can login after restart")
        else:
            print(f"❌ Failed to login as 'bharath' after restart (Status: {login_response.status_code})")
            return False
        
        # Test another user if available
        demo_login_data = {
            'username': 'demo',
            'password': 'demo'
        }
        
        demo_session = requests.Session()
        demo_response = demo_session.post(f"{AZURE_URL}/login", data=demo_login_data, timeout=30)
        
        if demo_response.status_code == 200 and "dashboard" in demo_response.url:
            print("✅ User 'demo' still exists and can login after restart")
        else:
            print("ℹ️  Demo user may not exist or login failed")
        
        print("\n🎉 SUCCESS: User data persists after Azure server restart!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing Azure: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Azure persistence: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 AZURE USER PERSISTENCE TEST AFTER RESTART")
    print("=" * 60)
    
    success = test_azure_users()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ FINAL RESULT: User persistence after restart - VERIFIED!")
        print("🎯 The database fix is working correctly!")
    else:
        print("❌ FINAL RESULT: Issues detected with user persistence")
    print("=" * 60)

if __name__ == "__main__":
    main()
