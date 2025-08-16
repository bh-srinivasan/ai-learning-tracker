#!/usr/bin/env python3
"""
Test script to reproduce the dashboard Internal Server Error
by simulating non-admin user access
"""

import requests
import json

# Test URL
BASE_URL = "https://ai-learning-tracker-bharath.azurewebsites.net"

def test_dashboard_access():
    """Test dashboard access with different user scenarios"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("=== Testing Dashboard Access ===")
    
    # Test 1: Try to access dashboard without login
    print("\n1. Testing dashboard access without login...")
    try:
        response = session.get(f"{BASE_URL}/dashboard", timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.content)}")
        if response.status_code >= 400:
            print(f"Error Response: {response.text[:500]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Try to login as demo user first
    print("\n2. Testing login as demo user...")
    login_data = {
        'username': 'demo',
        'password': 'Demouserpass!2025'
    }
    
    try:
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=30)
        print(f"Login Status Code: {login_response.status_code}")
        print(f"Login Response Length: {len(login_response.content)}")
        
        if login_response.status_code == 200:
            print("Login successful, now testing dashboard access...")
            
            # Test dashboard access after login
            dashboard_response = session.get(f"{BASE_URL}/dashboard", timeout=30)
            print(f"Dashboard Status Code: {dashboard_response.status_code}")
            print(f"Dashboard Response Length: {len(dashboard_response.content)}")
            
            if dashboard_response.status_code >= 400:
                print(f"Dashboard Error Response: {dashboard_response.text[:1000]}...")
                
                # Check if it's a 500 error
                if dashboard_response.status_code == 500:
                    print("\n*** FOUND THE 500 INTERNAL SERVER ERROR ***")
                    print("This confirms the dashboard issue exists")
                    
        else:
            print(f"Login failed: {login_response.text[:500]}...")
            
    except Exception as e:
        print(f"Error during login/dashboard test: {e}")
    
    # Test 3: Check if app is responding to basic requests
    print("\n3. Testing basic app health...")
    try:
        health_response = session.get(f"{BASE_URL}/", timeout=30)
        print(f"Home page Status Code: {health_response.status_code}")
        print(f"Home page Response Length: {len(health_response.content)}")
    except Exception as e:
        print(f"Error accessing home page: {e}")

if __name__ == "__main__":
    test_dashboard_access()
