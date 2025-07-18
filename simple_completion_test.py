"""
Simple Course Completion Test
============================

Test course completion feature directly with proper authentication.
"""

import requests
import os

def test_course_completion_simple():
    """Simple test for course completion."""
    
    # Create session
    session = requests.Session()
    
    print("🧪 Testing Course Completion Fix")
    print("=" * 40)
    
    try:
        # Get login page first to establish session
        print("1. Getting login page...")
        login_page = session.get("http://localhost:5000/login")
        print(f"   Status: {login_page.status_code}")
        
        # Login with demo credentials
        print("2. Logging in as demo user...")
        login_data = {
            'username': 'demo',
            'password': 'demo123'
        }
        
        login_response = session.post("http://localhost:5000/login", data=login_data)
        print(f"   Login response status: {login_response.status_code}")
        print(f"   Final URL: {login_response.url}")
        
        # Check if we're redirected to dashboard (successful login)
        if "/dashboard" in login_response.url or login_response.status_code == 302:
            print("   ✅ Login successful")
            
            # Get dashboard to see available courses
            print("3. Getting dashboard...")
            dashboard = session.get("http://localhost:5000/dashboard")
            print(f"   Dashboard status: {dashboard.status_code}")
            
            if dashboard.status_code == 200:
                print("   ✅ Dashboard loaded")
                
                # Try to complete course ID 1 (if it exists)
                print("4. Testing course completion...")
                completion_response = session.post(
                    "http://localhost:5000/complete-course/1",
                    headers={'X-Requested-With': 'XMLHttpRequest'}
                )
                
                print(f"   Completion status: {completion_response.status_code}")
                print(f"   Response text: {completion_response.text}")
                
                if completion_response.status_code == 200:
                    try:
                        result = completion_response.json()
                        if result.get('success'):
                            print("   ✅ Course completion successful!")
                            print(f"   🎊 Points: {result.get('points_earned')}")
                            print(f"   📈 Level: {result.get('new_level')}")
                        else:
                            print(f"   ❌ Completion failed: {result.get('message')}")
                    except:
                        print("   ⚠️  Non-JSON response (might be form submission)")
                        # Try the form submission endpoint
                        form_completion = session.post("http://localhost:5000/mark-complete/1")
                        print(f"   Form completion status: {form_completion.status_code}")
                        
                        if form_completion.status_code == 302:
                            print("   ✅ Form completion successful (redirected)")
                        else:
                            print(f"   Response: {form_completion.text[:200]}...")
                
            else:
                print("   ❌ Dashboard load failed")
        else:
            print("   ❌ Login failed")
            print(f"   Response content: {login_response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_course_completion_simple()
