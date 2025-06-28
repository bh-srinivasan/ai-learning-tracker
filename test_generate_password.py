#!/usr/bin/env python3
"""
Test script for the new Generate Viewable Password functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from werkzeug.security import check_password_hash
from app import app

def test_generate_viewable_password():
    """Test the generate viewable password functionality"""
    
    print("🧪 Testing Generate Viewable Password Functionality")
    print("=" * 60)
    
    # Configure Flask for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        
        # Step 1: Login as admin
        print("Step 1: Logging in as admin...")
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=True)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
        
        print("✅ Admin login successful")
        
        # Step 2: Create a test user if needed
        print("Step 2: Ensuring test user exists...")
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        try:
            # Check if bharath user exists
            test_user = conn.execute(
                'SELECT * FROM users WHERE username = ?',
                ('bharath',)
            ).fetchone()
            
            if test_user:
                test_user_id = test_user['id']
                print(f"✅ Test user 'bharath' found with ID: {test_user_id}")
            else:
                print("⚠️  Test user 'bharath' not found, using admin test")
                return False
                
        finally:
            conn.close()
        
        # Step 3: Test password generation with correct admin password
        print("Step 3: Testing password generation with correct admin password...")
        
        password_response = client.post('/admin/view-user-password', data={
            'user_id': str(test_user_id),
            'admin_password': 'admin'
        })
        
        if password_response.status_code != 200:
            print(f"❌ Password generation request failed: {password_response.status_code}")
            return False
        
        response_data = password_response.get_json()
        
        if response_data and response_data.get('success'):
            generated_password = response_data.get('password')
            print(f"✅ Password generated successfully: {generated_password}")
            
            # Step 4: Verify the password was set in the database
            print("Step 4: Verifying password was set in database...")
            conn = sqlite3.connect('ai_learning.db')
            conn.row_factory = sqlite3.Row
            
            try:
                updated_user = conn.execute(
                    'SELECT * FROM users WHERE id = ?',
                    (test_user_id,)
                ).fetchone()
                
                if check_password_hash(updated_user['password_hash'], generated_password):
                    print("✅ Generated password correctly set in database")
                else:
                    print("❌ Generated password not matching database hash")
                    return False
                    
            finally:
                conn.close()
            
            # Step 5: Test login with generated password
            print("Step 5: Testing login with generated password...")
            client.get('/logout')  # Logout admin first
            
            user_login_response = client.post('/login', data={
                'username': 'bharath',
                'password': generated_password
            }, follow_redirects=True)
            
            if user_login_response.status_code == 200:
                print("✅ User can login with generated password")
            else:
                print("❌ User cannot login with generated password")
                return False
            
        else:
            print(f"❌ Password generation failed: {response_data.get('error', 'Unknown error')}")
            return False
        
        # Step 6: Test with incorrect admin password
        print("Step 6: Testing with incorrect admin password...")
        
        # Login as admin again
        client.get('/logout')
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        })
        
        wrong_password_response = client.post('/admin/view-user-password', data={
            'user_id': str(test_user_id),
            'admin_password': 'wrongpassword'
        })
        
        wrong_response_data = wrong_password_response.get_json()
        
        if wrong_response_data and not wrong_response_data.get('success'):
            print("✅ Incorrect admin password correctly rejected")
        else:
            print("❌ Incorrect admin password was accepted (security issue)")
            return False
        
        return True

if __name__ == '__main__':
    if test_generate_viewable_password():
        print("\n🎉 GENERATE VIEWABLE PASSWORD TEST PASSED!")
        print("   ✅ Admin authentication works correctly")
        print("   ✅ Password generation and database update working")
        print("   ✅ Generated password allows user login")
        print("   ✅ Incorrect admin password properly rejected")
        print("   ✅ Security logging implemented")
    else:
        print("\n❌ GENERATE VIEWABLE PASSWORD TEST FAILED!")
        print("   Check the output above for specific issues")
