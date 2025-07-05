#!/usr/bin/env python3
"""
Update Azure User Passwords to Match Environment Variables
========================================================

This script updates the existing user passwords in the Azure database 
to match the environment variables you set.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def update_user_passwords():
    """Update user passwords to match environment variables"""
    print("🔄 UPDATING USER PASSWORDS TO MATCH ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    # Get environment variable values (using your .env values as fallback)
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    demo_username = os.environ.get('DEMO_USERNAME', 'demo') 
    demo_password = os.environ.get('DEMO_PASSWORD', 'DemoUserPassword123!')
    
    print(f"📋 Environment Variables:")
    print(f"   ADMIN_PASSWORD: {'*' * len(admin_password)} (loaded)")
    print(f"   DEMO_USERNAME: {demo_username}")
    print(f"   DEMO_PASSWORD: {'*' * len(demo_password)} (loaded)")
    
    # Connect to database
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        # Generate new password hashes
        admin_hash = generate_password_hash(admin_password)
        demo_hash = generate_password_hash(demo_password)
        
        print(f"\n🔐 Updating user passwords...")
        
        # Update admin password
        cursor = conn.execute('SELECT username FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone():
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                        (admin_hash, 'admin'))
            print("✅ Updated admin password")
        else:
            # Create admin user if doesn't exist
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                        ('admin', admin_hash))
            print("✅ Created admin user")
        
        # Update demo password
        cursor = conn.execute('SELECT username FROM users WHERE username = ?', (demo_username,))
        if cursor.fetchone():
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                        (demo_hash, demo_username))
            print(f"✅ Updated {demo_username} password")
        else:
            # Create demo user if doesn't exist
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                        (demo_username, demo_hash))
            print(f"✅ Created {demo_username} user")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n🎉 PASSWORD UPDATE COMPLETE!")
        print(f"✅ Users now use environment variable passwords")
        print(f"✅ Old fallback passwords are replaced")
        
        print(f"\n🔑 Updated Credentials:")
        print(f"   Admin: admin / {admin_password}")
        print(f"   Demo:  {demo_username} / {demo_password}")
        
        print(f"\n💡 Protected Users (unchanged):")
        print(f"   bharath: bharath / bharath (protected from scripts)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating passwords: {e}")
        return False

def main():
    if update_user_passwords():
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Commit and push changes to Azure:")
        print(f"   git add .")
        print(f"   git commit -m 'Update user passwords to use environment variables'")
        print(f"   git push azure master")
        print(f"2. Test the new passwords:")
        print(f"   python test_env_variables.py")
    else:
        print(f"\n❌ Password update failed. Please check the error above.")

if __name__ == "__main__":
    main()
