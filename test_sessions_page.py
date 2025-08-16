import requests
import os

# Test the admin sessions page
def test_admin_sessions_page():
    base_url = "http://127.0.0.1:5000"
    
    # Create a session
    session = requests.Session()
    
    print("1. Logging in as admin...")
    login_data = {
        'username': 'admin',
        'password': os.getenv('ADMIN_PASSWORD', 'admin123')  # Use environment or default
    }
    
    response = session.post(f"{base_url}/login", data=login_data)
    print(f"Login response: {response.status_code}")
    
    if response.status_code == 200 and "admin" in response.text.lower():
        print("✅ Login successful")
        
        print("2. Accessing admin sessions page...")
        sessions_response = session.get(f"{base_url}/admin/sessions")
        print(f"Sessions page response: {sessions_response.status_code}")
        
        if sessions_response.status_code == 200:
            # Check if the page contains the expected sections
            content = sessions_response.text
            if "Activity Types" in content:
                print("✅ Activity Types section found")
            else:
                print("❌ Activity Types section NOT found")
                
            if "Daily Logins" in content:
                print("✅ Daily Logins section found")
            else:
                print("❌ Daily Logins section NOT found")
                
            # Check for "No data" messages
            if "No activity data available" in content:
                print("❌ Activity data shows 'No data available'")
            else:
                print("✅ Activity data appears to be present")
                
            if "No login data available" in content:
                print("❌ Login data shows 'No data available'")
            else:
                print("✅ Login data appears to be present")
        else:
            print(f"❌ Failed to access sessions page: {sessions_response.status_code}")
    else:
        print("❌ Login failed")

if __name__ == '__main__':
    test_admin_sessions_page()
