#!/usr/bin/env python3
"""
Safe Password Reset Script
Resets passwords while protecting admin users from modification during testing
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Protected users that should not be modified during testing
PROTECTED_USERS = ['bharath']

def is_protected_user(username):
    """Check if user is protected from password resets"""
    return username in PROTECTED_USERS

def reset_user_password(username, password, display_name, force=False):
    """Reset a user's password with protection checks"""
    
    # Check if user is protected
    if is_protected_user(username) and not force:
        print(f"🛡️  {display_name} user '{username}' is protected - skipping password reset")
        print(f"💡 Use force=True if you really need to reset this user's password")
        return True  # Return success to not break the flow
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"👤 {display_name} user '{username}' not found - creating new user")
            
            # Create new user
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, level, points, status) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, 'Beginner', 0, 'active'))
            
            print(f"✅ {display_name} user created successfully")
        else:
            print(f"👤 Found {display_name} user with ID: {user[0]}")
            
            # Update password
            password_hash = generate_password_hash(password)
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE username = ?
            ''', (password_hash, username))
            
            print(f"✅ {display_name} password updated successfully")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error updating {display_name} password: {e}")
        return False

def main():
    """Reset passwords with protection for admin users"""
    print("🔐 AI Learning Tracker - Safe Password Reset")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    admin_password = os.environ.get('ADMIN_PASSWORD')
    demo_username = os.environ.get('DEMO_USERNAME', 'demo')
    demo_password = os.environ.get('DEMO_PASSWORD')
    
    print("🔍 Environment Variables Status:")
    print(f"   ADMIN_PASSWORD: {'SET' if admin_password else 'NOT SET'}")
    print(f"   DEMO_USERNAME: {demo_username}")
    print(f"   DEMO_PASSWORD: {'SET' if demo_password else 'NOT SET'}")
    
    print(f"\n🛡️  Protected Users: {', '.join(PROTECTED_USERS)}")
    print("   (These users will be skipped during testing)")
    
    if not admin_password or not demo_password:
        print("\n❌ Missing required environment variables")
        return
    
    print("\n🔄 Resetting passwords...")
    
    # Reset admin password (primary admin)
    admin_success = reset_user_password('admin', admin_password, 'Admin')
    
    # Reset demo user password (for testing)
    demo_success = reset_user_password(demo_username, demo_password, 'Demo')
    
    # Show bharath status without modifying
    print(f"\n🛡️  Protected user 'bharath' - password unchanged")
    
    print("\n" + "=" * 50)
    print("📊 Password Reset Results:")
    print(f"   Admin User:     {'✅ SUCCESS' if admin_success else '❌ FAILED'}")
    print(f"   Demo User:      {'✅ SUCCESS' if demo_success else '❌ FAILED'}")
    print(f"   Protected User: 🛡️  PROTECTED (bharath)")
    
    if admin_success and demo_success:
        print("\n🎉 Password reset completed successfully!")
        print("\n🔑 Available Login Credentials:")
        print(f"   👤 Admin:     admin / {admin_password}")
        print(f"   👤 Demo:      {demo_username} / {demo_password}")
        print(f"   👤 Protected: bharath / [unchanged]")
        
        print("\n💡 Usage Guidelines:")
        print("   - Use 'admin' for administrative tasks")
        print(f"   - Use '{demo_username}' for testing and validation")
        print("   - 'bharath' is protected for production use")
        
        print("\n🌐 Login at: http://localhost:5000")
    else:
        print("\n❌ Some password resets failed!")

if __name__ == "__main__":
    main()
