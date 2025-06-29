#!/usr/bin/env python3
"""
Reset Both Admin and Demo User Passwords
Updates both users to use passwords from environment variables
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

def reset_user_password(username, password, display_name):
    """Reset a user's password"""
    try:
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
    """Reset both user passwords"""
    print("🔐 AI Learning Tracker - Reset All User Passwords")
    print("=" * 55)
    
    # Load environment variables
    load_dotenv()
    
    admin_password = os.environ.get('ADMIN_PASSWORD')
    demo_password = os.environ.get('DEMO_PASSWORD')
    
    if not admin_password:
        print("❌ ADMIN_PASSWORD not found in environment")
        return
    
    if not demo_password:
        print("❌ DEMO_PASSWORD not found in environment")
        return
    
    print("🔍 Environment Variables Status:")
    print(f"   ADMIN_PASSWORD: {len(admin_password)} characters")
    print(f"   DEMO_PASSWORD: {len(demo_password)} characters")
    
    print("\n🔄 Resetting passwords...")
    
    # Reset admin password
    admin_success = reset_user_password('admin', admin_password, 'Admin')
    
    # Reset demo user password
    demo_success = reset_user_password('bharath', demo_password, 'Demo User')
    
    print("\n" + "=" * 55)
    print("📊 Password Reset Results:")
    print(f"   Admin User:  {'✅ SUCCESS' if admin_success else '❌ FAILED'}")
    print(f"   Demo User:   {'✅ SUCCESS' if demo_success else '❌ FAILED'}")
    
    if admin_success and demo_success:
        print("\n🎉 All passwords reset successfully!")
        print("\n🔑 Updated Login Credentials:")
        print(f"   👤 Admin:  admin / {admin_password}")
        print(f"   👤 Demo:   bharath / {demo_password}")
        print("\n🌐 Login at: http://localhost:5000")
        print("\n💡 Next Steps:")
        print("   1. Test login with both accounts")
        print("   2. Clear browser cache if needed")
        print("   3. Restart Flask app if it's running")
    else:
        print("\n❌ Some password resets failed!")

if __name__ == "__main__":
    main()
