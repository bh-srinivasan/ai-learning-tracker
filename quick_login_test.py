import requests

# Direct test of admin login
session = requests.Session()

try:
    print("Testing admin login...")
    
    response = session.post(
        'https://ai-learning-tracker-bharath.azurewebsites.net/login',
        data={'username': 'admin', 'password': 'admin'},
        timeout=60,
        allow_redirects=False
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Location: {response.headers.get('Location', 'None')}")
    
    if response.status_code == 302:
        print("✅ Login successful - redirect detected")
        
        # Test accessing admin dashboard with the session
        admin_response = session.get(
            'https://ai-learning-tracker-bharath.azurewebsites.net/admin',
            timeout=30
        )
        
        print(f"Admin dashboard status: {admin_response.status_code}")
        
        if "Please log in to access" in admin_response.text:
            print("❌ Still getting access denied")
        else:
            print("✅ Admin dashboard accessible!")
            
    else:
        print(f"❌ Login failed with status {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
