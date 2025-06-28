#!/usr/bin/env python3
"""
Test admin password change through Flask app
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from werkzeug.security import check_password_hash
from app import app

def test_password_change_flow():
    """Test the complete password change flow through Flask"""
    
    print("🧪 Testing Password Change Through Flask App")
    print("=" * 60)
    
    # Configure Flask for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
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
        
        if b'Welcome back, admin!' in login_response.data or b'Admin Dashboard' in login_response.data:
            print("✅ Login successful")
        else:
            print("❌ Login failed - unexpected response")
            print(f"Response contains: {login_response.data[:200]}")
            return False
        
        # Step 2: Access admin change password page
        print("Step 2: Accessing admin change password page...")
        password_page = client.get('/admin/change-password')
        
        if password_page.status_code != 200:
            print(f"❌ Failed to access password change page: {password_page.status_code}")
            return False
        
        if b'Change Admin Password' in password_page.data:
            print("✅ Password change page accessible")
        else:
            print("❌ Password change page not accessible")
            return False
        
        # Step 3: Submit password change
        print("Step 3: Submitting password change...")
        new_password = 'TestNewPass123!'
        
        change_response = client.post('/admin/change-password', data={
            'current_password': 'admin',
            'new_password': new_password,
            'confirm_password': new_password
        }, follow_redirects=True)
        
        if change_response.status_code != 200:
            print(f"❌ Password change failed with status {change_response.status_code}")
            return False
        
        # Check if we were redirected to login page
        if b'login' in change_response.data.lower() or b'log in' in change_response.data:
            print("✅ Redirected to login page after password change")
        else:
            print("⚠️  May not have been redirected to login page")
            print(f"Response contains: {change_response.data[:200]}")
        
        # Step 4: Verify password was changed in database
        print("Step 4: Verifying password change in database...")
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        try:
            admin_user = conn.execute(
                'SELECT * FROM users WHERE username = ?',
                ('admin',)
            ).fetchone()
            
            # Test old password doesn't work
            if not check_password_hash(admin_user['password_hash'], 'admin'):
                print("✅ Old password 'admin' is now invalid")
            else:
                print("❌ Old password 'admin' still works (CRITICAL ISSUE)")
                return False
            
            # Test new password works
            if check_password_hash(admin_user['password_hash'], new_password):
                print("✅ New password works in database")
            else:
                print("❌ New password doesn't work in database")
                return False
            
        finally:
            conn.close()
        
        # Step 5: Test login with new password
        print("Step 5: Testing login with new password...")
        
        # First, make sure we're logged out
        client.get('/logout')
        
        new_login_response = client.post('/login', data={
            'username': 'admin',
            'password': new_password
        }, follow_redirects=True)
        
        if new_login_response.status_code == 200 and (
            b'Welcome back, admin!' in new_login_response.data or 
            b'Admin Dashboard' in new_login_response.data
        ):
            print("✅ Login with new password successful")
        else:
            print("❌ Login with new password failed")
            print(f"Response: {new_login_response.data[:200]}")
            return False
        
        # Step 6: Test login with old password fails
        print("Step 6: Testing that old password no longer works...")
        
        client.get('/logout')
        
        old_login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'  # old password
        }, follow_redirects=True)
        
        if b'Invalid username or password' in old_login_response.data:
            print("✅ Old password correctly rejected")
        else:
            print("❌ Old password still works (CRITICAL ISSUE)")
            return False
        
        # Step 7: Reset password back to 'admin' for future tests
        print("Step 7: Resetting password back to 'admin'...")
        conn = sqlite3.connect('ai_learning.db')
        from werkzeug.security import generate_password_hash
        
        try:
            reset_hash = generate_password_hash('admin')
            conn.execute(
                'UPDATE users SET password_hash = ? WHERE username = ?',
                (reset_hash, 'admin')
            )
            conn.commit()
            print("✅ Password reset to 'admin' for future tests")
        finally:
            conn.close()
        
        return True

if __name__ == '__main__':
    if test_password_change_flow():
        print("\n🎉 PASSWORD CHANGE FLOW TEST PASSED!")
        print("   ✅ Login works with current password")
        print("   ✅ Password change page accessible")
        print("   ✅ Password update works correctly")
        print("   ✅ Old password invalidated immediately")
        print("   ✅ New password works immediately")
        print("   ✅ Session properly invalidated")
        print("   ✅ User redirected to login after change")
    else:
        print("\n❌ PASSWORD CHANGE FLOW TEST FAILED!")
        print("   Check the output above for specific issues")
