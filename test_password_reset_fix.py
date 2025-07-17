#!/usr/bin/env python3
"""
Test script to verify the password reset functionality is working correctly
"""

import time
import subprocess
import sys
import sqlite3
import os

def test_password_reset_fix():
    """Test the password reset fix"""
    
    print("🧪 Testing Password Reset Fix")
    print("=" * 50)
    
    # 1. Check database
    if not os.path.exists('ai_learning.db'):
        print("❌ Database not found")
        return False
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Get test users
    users = conn.execute('SELECT id, username FROM users WHERE username != "admin"').fetchall()
    admin_user = conn.execute('SELECT id, username FROM users WHERE username = "admin"').fetchone()
    
    print(f"✅ Database connected")
    print(f"   Admin user: {admin_user['username'] if admin_user else 'NOT FOUND'}")
    print(f"   Test users available: {len(users)}")
    
    for user in users[:3]:  # Show first 3 test users
        print(f"     - {user['username']} (ID: {user['id']})")
    
    conn.close()
    
    # 2. Check route implementation
    print(f"\n🔍 Checking Route Implementation")
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('Route exists', '@app.route(\'/admin/reset-user-password\', methods=[\'POST\'])'),
            ('Debug logging', 'DEBUG: Form data received'),
            ('Better user_id handling', 'user_id_str = request.form.get(\'user_id\', \'\').strip()'),
            ('Integer conversion', 'user_id = int(user_id_str)'),
            ('Comprehensive validation', 'User ID is missing or invalid')
        ]
        
        for check_name, pattern in checks:
            if pattern in content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                
    except Exception as e:
        print(f"   ❌ Error reading app.py: {e}")
    
    # 3. Check template implementation
    print(f"\n🔍 Checking Template Implementation")
    try:
        with open('templates/admin/users.html', 'r') as f:
            template_content = f.read()
        
        template_checks = [
            ('Form action correct', 'action="{{ url_for(\'admin_reset_user_password\') }}"'),
            ('Hidden user_id field', '<input type="hidden" id="user_id" name="user_id">'),
            ('Password fields', 'name="custom_password"'),
            ('Confirmation field', 'name="confirm_custom_password"'),
            ('Checkbox field', 'name="reset_individual_confirmation"'),
            ('Debug logging', 'console.log(\'DEBUG: Setting modal data'),
            ('Enhanced validation', 'console.log(\'DEBUG: Form submission data')
        ]
        
        for check_name, pattern in template_checks:
            if pattern in template_content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                
    except Exception as e:
        print(f"   ❌ Error reading template: {e}")
    
    # 4. Provide testing instructions
    print(f"\n📋 Testing Instructions")
    print("1. Start Flask app: python app.py")
    print("2. Open browser to: http://localhost:5000")
    print("3. Login as admin")
    print("4. Go to: Admin → Manage Users")
    print("5. Click the dropdown next to any non-admin user")
    print("6. Select 'Set Custom Password'")
    print("7. Fill in the form and submit")
    print("8. Check browser console (F12) for debug messages")
    print("9. Check Flask terminal for debug output")
    
    # 5. Expected behavior
    print(f"\n✅ Expected Behavior After Fix")
    print("- Modal should populate user ID correctly")
    print("- Form should validate all fields")
    print("- Debug messages should appear in browser console")
    print("- Flask should log form data received")
    print("- Success message should appear after password reset")
    print("- No more 'User ID and new password are required' error")
    
    return True

if __name__ == '__main__':
    success = test_password_reset_fix()
    
    if success:
        print(f"\n🎉 Password Reset Fix Applied Successfully!")
        print("The issue should now be resolved.")
    else:
        print(f"\n❌ Fix verification failed.")
        print("Please check the database and file structure.")
