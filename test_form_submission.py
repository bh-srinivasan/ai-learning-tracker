#!/usr/bin/env python3
"""
Test the password reset form submission to debug the "User ID and new password are required" error
"""

import requests
import sqlite3
import os

def test_form_submission():
    """Test the actual form submission"""
    
    print("🧪 Testing Custom Password Reset Form Submission")
    print("=" * 60)
    
    # Check if we can connect to the running Flask app
    base_url = "http://localhost:5000"
    
    try:
        # Test if server is running
        response = requests.get(base_url, timeout=5)
        print(f"✅ Flask server is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Flask server not accessible: {e}")
        print("💡 Please run 'python app.py' in another terminal first")
        return False
    
    # Get database info for test
    if not os.path.exists('ai_learning.db'):
        print("❌ Database not found")
        return False
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Find a test user (non-admin)
    users = conn.execute('SELECT id, username FROM users WHERE username != "admin"').fetchall()
    conn.close()
    
    if not users:
        print("❌ No non-admin users found for testing")
        return False
    
    test_user = users[0]
    print(f"🎯 Using test user: {test_user['username']} (ID: {test_user['id']})")
    
    # Test the form data that would be sent
    form_data = {
        'user_id': str(test_user['id']),  # This might be the issue - as string
        'custom_password': 'TestPass123!',
        'confirm_custom_password': 'TestPass123!',
        'reset_individual_confirmation': 'on'
    }
    
    print("\n📝 Form data being sent:")
    for key, value in form_data.items():
        if 'password' in key.lower():
            print(f"   {key}: {'*' * len(value)}")
        else:
            print(f"   {key}: {value} (type: {type(value).__name__})")
    
    # Test different user_id formats
    test_cases = [
        {'name': 'String ID', 'user_id': str(test_user['id'])},
        {'name': 'Integer ID', 'user_id': test_user['id']},
        {'name': 'Empty ID', 'user_id': ''},
        {'name': 'None ID', 'user_id': None}
    ]
    
    print("\n🔍 Testing different user_id formats:")
    for case in test_cases:
        test_data = form_data.copy()
        test_data['user_id'] = case['user_id']
        
        # Simulate the Flask route logic
        user_id = None
        try:
            if case['user_id'] is not None and case['user_id'] != '':
                user_id = int(case['user_id'])
        except (ValueError, TypeError):
            user_id = None
        
        result = "✅ PASS" if user_id is not None else "❌ FAIL"
        print(f"   {case['name']}: user_id={case['user_id']} → converted={user_id} {result}")
    
    return True

def check_javascript_logic():
    """Check the JavaScript modal logic"""
    print("\n🔍 Checking JavaScript Modal Logic")
    print("=" * 50)
    
    try:
        with open('templates/admin/users.html', 'r') as f:
            content = f.read()
        
        # Check if the modal event listener exists
        if "getElementById('resetPasswordModal').addEventListener('show.bs.modal'" in content:
            print("✅ Modal event listener found")
            
            # Check if user ID is being set
            if "modal.querySelector('#user_id').value = userId;" in content:
                print("✅ User ID is being set in modal")
            else:
                print("❌ User ID setting logic not found")
                
            # Check if button has the data attributes
            if 'data-user-id="{{ user.id }}"' in content:
                print("✅ Button has data-user-id attribute")
            else:
                print("❌ Button missing data-user-id attribute")
                
        else:
            print("❌ Modal event listener not found")
            
    except Exception as e:
        print(f"❌ Error checking template: {e}")

if __name__ == '__main__':
    success = test_form_submission()
    check_javascript_logic()
    
    if success:
        print("\n💡 Recommendations:")
        print("1. Ensure Flask server is running")
        print("2. Check browser developer tools for JavaScript errors")
        print("3. Verify the modal is properly setting the user_id")
        print("4. Check if the form is submitting all required fields")
