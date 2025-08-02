"""
Force Azure database initialization via HTTP requests
"""
import requests
import time

def force_azure_init():
    """Try different initialization approaches for Azure"""
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print("🔄 Attempting to force Azure database initialization...")
    
    # Method 1: Try the init-admin endpoint with correct password
    print("\n1️⃣ Trying init-admin endpoint...")
    try:
        response = requests.get(f"{base_url}/init-admin?password=YourSecureAdminPassword1223!", timeout=60)
        print(f"Status: {response.status_code}")
        if "Admin user created successfully" in response.text:
            print("✅ Admin user created successfully!")
        elif "Admin user already exists" in response.text:
            print("ℹ️ Admin user already exists")
        else:
            print(f"Response: {response.text[:500]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 2: Try direct login to see if admin exists
    print("\n2️⃣ Testing admin login...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'YourSecureAdminPassword123!'
        }
        response = requests.post(f"{base_url}/login", data=login_data, timeout=60)
        print(f"Login status: {response.status_code}")
        if response.status_code == 200:
            if "Welcome back" in response.text:
                print("✅ Login successful!")
            elif "Admin Dashboard" in response.text:
                print("✅ Login successful, redirected to admin!")
            else:
                print("⚠️ Login response unclear")
        else:
            print(f"❌ Login failed: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Method 3: Try to hit the home page to trigger initialization
    print("\n3️⃣ Checking homepage...")
    try:
        response = requests.get(base_url, timeout=30)
        print(f"Homepage status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Homepage accessible")
        else:
            print("❌ Homepage not accessible")
    except Exception as e:
        print(f"❌ Homepage error: {e}")

if __name__ == '__main__':
    force_azure_init()
