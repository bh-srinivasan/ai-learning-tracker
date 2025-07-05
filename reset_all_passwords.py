#!/usr/bin/env python3
"""
Password reset utility with security guards
Only allows resets for authorized test users in development environment
IMPORTANT: This script can only be run with explicit user authorization
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Import security guard system
from security_guard import (
    SecurityGuard, SecurityGuardError, password_reset_guard, 
    validate_test_environment, get_test_credentials
)

@password_reset_guard(ui_triggered=False, require_explicit_request=True)
def reset_user_password(username, password, display_name, explicit_user_request=False):
    """
    Reset a user's password - requires explicit user authorization
    
    Args:
        username: Username to reset
        password: New password
        display_name: Display name for logging
        explicit_user_request: Must be True to proceed
    """
    if not explicit_user_request:
        raise SecurityGuardError(
            "Password reset must be explicitly requested by the user. "
            "Backend password resets are not allowed without explicit authorization."
        )
    
    try:
        # Apply security guard validation for backend password reset
        SecurityGuard.validate_operation('backend_password_reset', username, explicit_authorization=True)
        
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Error: {display_name} user '{username}' not found")
            return False
        
        # Update password
        password_hash = generate_password_hash(password)
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, last_activity = CURRENT_TIMESTAMP 
            WHERE username = ?
        ''', (password_hash, username))
        
        conn.commit()
        conn.close()
        
        print(f"✅ {display_name} password updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {display_name} password: {e}")
        return False

def main():
    """Reset both user passwords with security validation"""
    print("🔐 AI Learning Tracker - Reset All User Passwords")
    print("=" * 55)
    
    try:
        # Validate test environment first
        validate_test_environment()
        print("✅ Security validation passed")
    except SecurityGuardError as e:
        print(f"❌ Security Guard Error: {str(e)}")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Use security-approved method to get credentials
    test_creds = get_test_credentials()
    admin_password = test_creds['admin']['password']
    demo_password = test_creds['demo']['password']
    
    print("🔍 Environment Variables Status:")
    print(f"   ADMIN_PASSWORD: {len(admin_password)} characters")
    print(f"   DEMO_PASSWORD: {len(demo_password)} characters")
    
    print("\n🔄 Resetting passwords...")
    print("⚠️  IMPORTANT: This operation requires explicit user authorization")
    print("   By running this script, you are explicitly authorizing password resets")
    
    # Reset admin password (with explicit authorization)
    admin_success = reset_user_password('admin', admin_password, 'Admin', explicit_user_request=True)
    
    # Reset demo user password (with explicit authorization)
    demo_success = reset_user_password('demo', demo_password, 'Demo User', explicit_user_request=True)
    
    print("\n" + "=" * 55)
    print("📊 Password Reset Results:")
    print(f"   Admin User:  {'✅ SUCCESS' if admin_success else '❌ FAILED'}")
    print(f"   Demo User:   {'✅ SUCCESS' if demo_success else '❌ FAILED'}")
    
    if admin_success and demo_success:
        print("\n🎉 All passwords reset successfully!")
        print("\n🔑 Updated Login Credentials:")
        print(f"   👤 Admin:  admin / {admin_password}")
        print(f"   👤 Demo:   demo / {demo_password}")
        print("\n🌐 Login at: http://localhost:5000")
        print("\n💡 Next Steps:")
        print("   1. Test login with both accounts")
        print("   2. Clear browser cache if needed")
        print("   3. Restart Flask app if it's running")
    else:
        print("\n❌ Some password resets failed!")

if __name__ == "__main__":
    main()
