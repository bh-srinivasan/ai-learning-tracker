#!/usr/bin/env python3
"""
Debug script to test the custom password reset functionality
"""

import sqlite3
import sys
import os

def test_password_reset_flow():
    """Test the password reset flow by checking form fields and data"""
    
    print("🔍 Debugging Custom Password Reset Flow")
    print("=" * 50)
    
    # Check if database exists
    db_path = 'ai_learning.db'
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    # Connect to database and check users
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get all users
        users = conn.execute('SELECT id, username, status FROM users').fetchall()
        
        print("📊 Available Users:")
        for user in users:
            print(f"   ID: {user['id']}, Username: {user['username']}, Status: {user['status']}")
        
        print("\n✅ Database connection successful")
        
        # Test non-admin user for password reset
        test_user = None
        for user in users:
            if user['username'] != 'admin':
                test_user = user
                break
        
        if test_user:
            print(f"\n🎯 Test Target User: {test_user['username']} (ID: {test_user['id']})")
            
            # Simulate form data
            form_data = {
                'user_id': test_user['id'],
                'custom_password': 'TestPass123!',
                'confirm_custom_password': 'TestPass123!',
                'reset_individual_confirmation': 'on'
            }
            
            print("\n📝 Simulated Form Data:")
            for key, value in form_data.items():
                if 'password' in key.lower():
                    print(f"   {key}: {'*' * len(str(value))}")
                else:
                    print(f"   {key}: {value}")
            
            # Test field validation logic
            print("\n🔍 Field Validation:")
            user_id = form_data.get('user_id')
            custom_password = form_data.get('custom_password', '').strip()
            confirm_password = form_data.get('confirm_custom_password', '').strip()
            confirmation_checked = form_data.get('reset_individual_confirmation')
            
            print(f"   user_id type: {type(user_id)} value: {user_id}")
            print(f"   custom_password length: {len(custom_password)}")
            print(f"   confirm_password length: {len(confirm_password)}")
            print(f"   confirmation_checked: {confirmation_checked}")
            
            # Validate conditions
            validation_results = {
                'user_id_exists': bool(user_id),
                'password_not_empty': bool(custom_password),
                'confirm_not_empty': bool(confirm_password),
                'passwords_match': custom_password == confirm_password,
                'confirmation_checked': bool(confirmation_checked)
            }
            
            print("\n✅ Validation Results:")
            for check, result in validation_results.items():
                status = "✅" if result else "❌"
                print(f"   {status} {check}: {result}")
            
            if all(validation_results.values()):
                print("\n🎉 All validations PASSED - Form should work correctly!")
            else:
                print("\n❌ Some validations FAILED - This would cause errors!")
                
        else:
            print("\n⚠️  No non-admin users found for testing")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()
    
    return True

def check_route_structure():
    """Check the route implementation"""
    print("\n🔍 Checking Route Implementation")
    print("=" * 50)
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
        # Look for the route
        if '@app.route(\'/admin/reset-user-password\', methods=[\'POST\'])' in content:
            print("✅ Route endpoint found")
            
            # Check field access patterns
            patterns = [
                'request.form.get(\'user_id\'',
                'request.form.get(\'custom_password\'',
                'request.form.get(\'confirm_custom_password\'',
                'request.form.get(\'reset_individual_confirmation\')'
            ]
            
            for pattern in patterns:
                if pattern in content:
                    print(f"✅ Found field access: {pattern}")
                else:
                    print(f"❌ Missing field access: {pattern}")
                    
        else:
            print("❌ Route endpoint not found")
            
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")

if __name__ == '__main__':
    print("🧪 Custom Password Reset Debug Test")
    print("=" * 60)
    
    success = test_password_reset_flow()
    check_route_structure()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Run the Flask app: python app.py")
        print("2. Login as admin")
        print("3. Go to Admin -> Manage Users")
        print("4. Try the 'Set Custom Password' option")
        print("5. Check if the issue persists")
    else:
        print("\n❌ Debug test failed - fix database issues first")
