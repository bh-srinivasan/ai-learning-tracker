#!/usr/bin/env python3
"""
Debug login functionality
"""

import requests
import sys

def test_login_debug():
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("Testing login functionality...")
    
    # Test admin login
    print("\n--- Testing Admin Login ---")
    login_url = f"{base_url}/login"
    login_data = {
        'username': 'admin',
        'password': 'admin'
    }
    
    response = session.post(login_url, data=login_data, allow_redirects=False)
    print(f"Admin login response: {response.status_code}")
    print(f"Location header: {response.headers.get('Location', 'None')}")
    
    if response.status_code in [302, 303]:
        # Follow redirect
        redirect_url = response.headers.get('Location')
        if redirect_url:
            if redirect_url.startswith('/'):
                redirect_url = base_url + redirect_url
            redirect_response = session.get(redirect_url)
            print(f"Redirect response: {redirect_response.status_code}")
            print(f"Contains 'admin' or 'dashboard': {'admin' in redirect_response.text.lower() or 'dashboard' in redirect_response.text.lower()}")
    
    # Test user login
    print("\n--- Testing User Login ---")
    session2 = requests.Session()
    login_data2 = {
        'username': 'bharath',
        'password': 'bharath'
    }
    
    response2 = session2.post(login_url, data=login_data2, allow_redirects=False)
    print(f"User login response: {response2.status_code}")
    print(f"Location header: {response2.headers.get('Location', 'None')}")
    
    if response2.status_code in [302, 303]:
        # Follow redirect
        redirect_url = response2.headers.get('Location')
        if redirect_url:
            if redirect_url.startswith('/'):
                redirect_url = base_url + redirect_url
            redirect_response = session2.get(redirect_url)
            print(f"Redirect response: {redirect_response.status_code}")
            print(f"Contains 'dashboard': {'dashboard' in redirect_response.text.lower()}")
    elif response2.status_code == 200:
        print("Login returned 200 - checking for error messages or form")
        if 'error' in response2.text.lower() or 'invalid' in response2.text.lower():
            print("ERROR: Login failed - error message found")
        elif 'login' in response2.text.lower() and 'form' in response2.text.lower():
            print("ERROR: Still on login page - credentials might be wrong")
        else:
            print("Unexpected 200 response content")

if __name__ == "__main__":
    test_login_debug()
