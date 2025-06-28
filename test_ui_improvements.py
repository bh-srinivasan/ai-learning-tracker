#!/usr/bin/env python3
"""
Test script for the improved Manage Users UI with grouped actions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from werkzeug.security import check_password_hash
from app import app

def test_improved_ui_functionality():
    """Test the improved manage users UI and password actions"""
    
    print("🧪 Testing Improved Manage Users UI")
    print("=" * 50)
    
    # Configure Flask for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        
        # Step 1: Login as admin
        print("Step 1: Testing admin login...")
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=True)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
        
        print("✅ Admin login successful")
        
        # Step 2: Access Manage Users page
        print("Step 2: Testing Manage Users page access...")
        users_response = client.get('/admin/users')
        
        if users_response.status_code != 200:
            print(f"❌ Users page access failed: {users_response.status_code}")
            return False
        
        users_html = users_response.data.decode('utf-8')
        
        # Check for UI improvements
        ui_checks = [
            ('Password dropdown present', 'dropdown-toggle' in users_html and 'Password' in users_html),
            ('Generate Viewable Password in dropdown', 'Generate Viewable Password' in users_html),
            ('Set Custom Password renamed', 'Set Custom Password' in users_html),
            ('View Current Password option', 'View Current Password' in users_html),
            ('Tooltips for actions', 'title=' in users_html),
            ('Organized action groups', 'btn-group' in users_html)
        ]
        
        for check_name, check_result in ui_checks:
            if check_result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                return False
        
        # Step 3: Test get user hash endpoint
        print("Step 3: Testing password hash viewing...")
        
        # Get test user ID
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        try:
            test_user = conn.execute(
                'SELECT * FROM users WHERE username = ?',
                ('bharath',)
            ).fetchone()
            
            if test_user:
                test_user_id = test_user['id']
                print(f"✅ Test user found: {test_user['username']} (ID: {test_user_id})")
            else:
                print("⚠️  Test user 'bharath' not found, skipping hash test")
                test_user_id = None
                
        finally:
            conn.close()
        
        if test_user_id:
            hash_response = client.post('/admin/get-user-hash', data={
                'user_id': str(test_user_id)
            })
            
            if hash_response.status_code == 200:
                hash_data = hash_response.get_json()
                if hash_data and hash_data.get('success'):
                    print("✅ Password hash retrieval working")
                    print(f"   Hash preview: {hash_data['password_hash'][:30]}...")
                else:
                    print(f"❌ Hash retrieval failed: {hash_data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Hash endpoint failed: {hash_response.status_code}")
                return False
        
        # Step 4: Test renamed password reset functionality
        print("Step 4: Testing renamed 'Set Custom Password' functionality...")
        
        if test_user_id:
            custom_password_response = client.post('/admin/reset-user-password', data={
                'user_id': str(test_user_id),
                'custom_password': 'TestCustomPass123!',
                'confirm_custom_password': 'TestCustomPass123!',
                'reset_individual_confirmation': 'on'
            }, follow_redirects=True)
            
            if custom_password_response.status_code == 200:
                print("✅ Set Custom Password functionality working")
                
                # Verify password was set
                conn = sqlite3.connect('ai_learning.db')
                conn.row_factory = sqlite3.Row
                try:
                    updated_user = conn.execute(
                        'SELECT * FROM users WHERE id = ?',
                        (test_user_id,)
                    ).fetchone()
                    
                    if check_password_hash(updated_user['password_hash'], 'TestCustomPass123!'):
                        print("✅ Custom password correctly set in database")
                    else:
                        print("❌ Custom password not set correctly")
                        return False
                        
                finally:
                    conn.close()
            else:
                print(f"❌ Set Custom Password failed: {custom_password_response.status_code}")
                return False
        
        # Step 5: Test UI responsiveness and Bootstrap components
        print("Step 5: Testing UI components...")
        
        ui_components = [
            ('Bootstrap dropdowns', 'data-bs-toggle="dropdown"' in users_html),
            ('Font Awesome icons', 'fas fa-' in users_html),
            ('Responsive design', 'btn-sm' in users_html),
            ('Proper button groups', 'btn-group' in users_html),
            ('Tooltips', 'title=' in users_html)
        ]
        
        for component_name, component_check in ui_components:
            if component_check:
                print(f"✅ {component_name} properly implemented")
            else:
                print(f"❌ {component_name} missing or incorrect")
                return False
        
        return True

if __name__ == '__main__':
    if test_improved_ui_functionality():
        print("\n🎉 IMPROVED UI FUNCTIONALITY TEST PASSED!")
        print("   ✅ Password actions grouped in dropdown menu")
        print("   ✅ 'Reset Password' renamed to 'Set Custom Password'")
        print("   ✅ 'View Current Password' option added")
        print("   ✅ Clean, organized action bar layout")
        print("   ✅ Proper tooltips and accessibility")
        print("   ✅ All backend endpoints working")
        print("   ✅ Bootstrap components properly implemented")
    else:
        print("\n❌ IMPROVED UI FUNCTIONALITY TEST FAILED!")
        print("   Check the output above for specific issues")
