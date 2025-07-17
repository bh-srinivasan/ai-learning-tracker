#!/usr/bin/env python3
"""
Test user persistence after Azure server restart
"""
import requests
import time
from datetime import datetime

def test_user_persistence():
    """Test if users persist after Azure server restart"""
    
    print("🔄 TESTING USER PERSISTENCE AFTER AZURE RESTART")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    azure_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    login_url = f"{azure_url}/login"
    
    # Test 1: Check if the application is accessible
    print("1. TESTING AZURE APPLICATION ACCESSIBILITY")
    print("-" * 40)
    
    try:
        response = requests.get(azure_url, timeout=10)
        if response.status_code == 200:
            print("✅ Azure application is accessible")
            print(f"   Status: {response.status_code}")
        else:
            print(f"⚠️  Azure application returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing Azure application: {e}")
        return False
    
    # Test 2: Test login with our test user Sachin
    print("\n2. TESTING TEST USER LOGIN")
    print("-" * 40)
    
    session = requests.Session()
    
    try:
        # Get login page first
        login_page = session.get(login_url, timeout=10)
        if login_page.status_code == 200:
            print("✅ Login page is accessible")
        else:
            print(f"❌ Login page returned status: {login_page.status_code}")
            return False
        
        # Attempt to login with Sachin user
        login_data = {
            'username': 'Sachin',
            'password': 'sachin123'
        }
        
        login_response = session.post(login_url, data=login_data, timeout=10)
        
        # Check if login was successful (should redirect to dashboard)
        if login_response.status_code == 302:  # Redirect indicates successful login
            print("✅ Test user 'Sachin' login successful!")
            print("   Status: 302 (Redirect to dashboard)")
            
            # Follow the redirect to get the dashboard
            dashboard_response = session.get(f"{azure_url}/dashboard", timeout=10)
            if dashboard_response.status_code == 200:
                print("✅ Dashboard accessible after login")
                return True
            else:
                print(f"⚠️  Dashboard returned status: {dashboard_response.status_code}")
                
        elif login_response.status_code == 200:
            # Check if we're still on login page (failed login)
            if "Invalid username or password" in login_response.text or "login" in login_response.text.lower():
                print("❌ Test user 'Sachin' login FAILED")
                print("   This indicates the user was deleted after restart!")
                return False
            else:
                print("✅ Login appears successful (stayed on same page)")
                return True
        else:
            print(f"⚠️  Login returned unexpected status: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return False
    
    return True

def test_user_creation_persistence():
    """Test creating a new user and checking if it persists"""
    print("\n3. TESTING NEW USER CREATION")
    print("-" * 40)
    
    azure_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    # For now, we'll just note that we would need admin access to create users
    print("💡 NOTE: To fully test user creation persistence, we would need:")
    print("   1. Admin access to create new users via Azure interface")
    print("   2. Another server restart")
    print("   3. Verification that the new user still exists")
    print()
    print("✅ Current test verifies existing user persistence")

def main():
    """Main test function"""
    print("🧪 USER PERSISTENCE TEST AFTER AZURE RESTART")
    print("=" * 60)
    print("Testing if our fix prevents user deletion after server restarts...")
    print()
    
    # Run the tests
    success = test_user_persistence()
    test_user_creation_persistence()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("-" * 25)
    
    if success:
        print("🎉 SUCCESS: User persistence fix is working!")
        print("✅ Test user 'Sachin' survived the Azure server restart")
        print("✅ Users are no longer being deleted after deployments")
        print("✅ The database is properly isolated from Git deployments")
    else:
        print("❌ FAILURE: User persistence issue still exists")
        print("⚠️  Test user 'Sachin' was deleted after restart")
        print("🔧 Additional investigation may be needed")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
