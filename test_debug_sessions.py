import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

def test_admin_sessions_with_debug():
    """Test admin sessions and save the response"""
    session = requests.Session()
    
    # First, try to get admin password from database
    import sqlite3
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    conn.close()
    
    print(f"Admin user found: {admin_user['username'] if admin_user else 'None'}")
    
    # Login
    login_data = {
        'username': 'admin',
        'password': 'admin123'  # Common default
    }
    
    print("Attempting login...")
    login_response = session.post('http://127.0.0.1:5000/login', data=login_data, allow_redirects=False)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code == 302:  # Redirect means success
        print("✅ Login successful (redirected)")
        
        # Now get admin sessions page
        sessions_response = session.get('http://127.0.0.1:5000/admin/sessions')
        print(f"Sessions response status: {sessions_response.status_code}")
        
        if sessions_response.status_code == 200:
            # Save the response to a file
            with open('debug_sessions_output.html', 'w', encoding='utf-8') as f:
                f.write(sessions_response.text)
            print("✅ Sessions page saved to debug_sessions_output.html")
            
            # Check key content
            content = sessions_response.text
            if 'activity_stats type:' in content:
                print("✅ Debug info found in response")
            if 'No activity data' in content:
                print("❌ Shows 'No activity data'")
            if 'No login data' in content:
                print("❌ Shows 'No login data'")
        else:
            print(f"❌ Failed to get sessions page: {sessions_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response content: {login_response.text[:200]}")

if __name__ == '__main__':
    test_admin_sessions_with_debug()
