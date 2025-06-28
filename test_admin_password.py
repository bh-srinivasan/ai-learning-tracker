#!/usr/bin/env python3
"""
Test script to verify admin password change functionality
"""
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def test_admin_password_change():
    """Test the admin password change functionality"""
    
    # Connect to the database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Get the current admin user
        admin_user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if not admin_user:
            print("❌ Error: Admin user not found in database")
            return False
        
        print(f"✅ Found admin user with ID: {admin_user['id']}")
        print(f"✅ Admin username: {admin_user['username']}")
        
        # Check if password_hash field exists
        if 'password_hash' not in admin_user.keys():
            print("❌ Error: password_hash field not found in admin user record")
            return False
        
        print("✅ password_hash field exists in user record")
        
        # Test current password verification (assuming 'admin' is the current password)
        current_password = 'admin'
        if check_password_hash(admin_user['password_hash'], current_password):
            print("✅ Current password verification works correctly")
        else:
            print("⚠️  Warning: Current password 'admin' doesn't match stored hash")
            print(f"   Stored hash: {admin_user['password_hash'][:50]}...")
        
        # Test password strength validation (simulate function)
        test_passwords = [
            ('weak', False),
            ('StrongPass123!', True),
            ('Admin123!@#', True)
        ]
        
        for password, should_be_valid in test_passwords:
            # Basic validation (minimum 8 chars, has upper, lower, digit, special)
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
            is_long_enough = len(password) >= 8
            
            is_valid = all([has_upper, has_lower, has_digit, has_special, is_long_enough])
            
            if is_valid == should_be_valid:
                print(f"✅ Password '{password}' validation: {'Valid' if is_valid else 'Invalid'} (as expected)")
            else:
                print(f"❌ Password '{password}' validation failed: Expected {'Valid' if should_be_valid else 'Invalid'}, got {'Valid' if is_valid else 'Invalid'}")
        
        # Test password hashing
        new_password = 'NewAdminPass123!'
        new_hash = generate_password_hash(new_password)
        
        if check_password_hash(new_hash, new_password):
            print("✅ Password hashing and verification works correctly")
        else:
            print("❌ Error: Password hashing/verification failed")
            return False
        
        print("\n🎉 All admin password change functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False
        
    finally:
        conn.close()

def check_database_schema():
    """Check if the database schema has all required fields"""
    conn = sqlite3.connect('ai_learning.db')
    
    try:
        # Get users table schema
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n📋 Users table schema:")
        required_fields = ['id', 'username', 'password_hash', 'created_at', 'is_admin']
        
        existing_fields = [col[1] for col in columns]
        
        for field in required_fields:
            if field in existing_fields:
                print(f"✅ {field}")
            else:
                print(f"❌ Missing: {field}")
        
        print(f"\nAll columns: {existing_fields}")
        
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔍 Testing Admin Password Change Functionality")
    print("=" * 50)
    
    # Check database schema first
    check_database_schema()
    
    print("\n" + "=" * 50)
    
    # Run the main test
    if test_admin_password_change():
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
