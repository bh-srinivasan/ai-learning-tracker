#!/usr/bin/env python3
"""
Admin Password Reset Script
Resets the admin password using the value from environment variables
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

def reset_admin_password():
    """Reset admin password using environment variable"""
    
    # Load environment variables
    load_dotenv()
    
    # Get admin password from environment
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if not admin_password:
        print("❌ Error: ADMIN_PASSWORD not found in environment variables")
        print("💡 Make sure your .env file contains ADMIN_PASSWORD=your_password")
        return False
    
    print(f"🔧 Resetting admin password...")
    print(f"📝 Using password from environment variable: {'*' * len(admin_password)}")
    
    try:
        # Connect to database
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute('SELECT id, username FROM users WHERE username = ?', ('admin',))
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("❌ Error: Admin user not found in database")
            print("💡 Creating admin user...")
            
            # Create admin user
            admin_hash = generate_password_hash(admin_password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, level, points, status) 
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', admin_hash, 'Expert', 1000, 'active'))
            
            print("✅ Admin user created successfully")
        else:
            print(f"👤 Found admin user with ID: {admin_user[0]}")
            
            # Update admin password
            admin_hash = generate_password_hash(admin_password)
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE username = ?
            ''', (admin_hash, 'admin'))
            
            print("✅ Admin password updated successfully")
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
        updated_user = cursor.fetchone()
        
        if updated_user:
            print(f"✅ Verification: Admin user exists with updated password hash")
            print(f"🔐 Password hash: {updated_user[1][:20]}...")
        
        conn.close()
        
        print("\n🎉 Password reset complete!")
        print(f"🔑 Admin login credentials:")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print(f"🌐 You can now login at: http://localhost:5000")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_env_password():
    """Verify the password in environment variables"""
    load_dotenv()
    
    admin_password = os.environ.get('ADMIN_PASSWORD')
    demo_password = os.environ.get('DEMO_PASSWORD')
    
    print("🔍 Current Environment Variable Status:")
    print("=" * 40)
    print(f"ADMIN_PASSWORD: {'SET (' + str(len(admin_password)) + ' chars)' if admin_password else 'NOT SET'}")
    print(f"DEMO_PASSWORD: {'SET (' + str(len(demo_password)) + ' chars)' if demo_password else 'NOT SET'}")
    
    if admin_password:
        print(f"\n📋 Admin password preview: {admin_password[:3]}{'*' * (len(admin_password) - 3)}")

def main():
    """Main function"""
    print("🔐 AI Learning Tracker - Admin Password Reset")
    print("=" * 50)
    
    # First verify environment variables
    verify_env_password()
    
    print("\n🔄 Proceeding with password reset...")
    
    # Reset the password
    success = reset_admin_password()
    
    if success:
        print("\n✅ Password reset completed successfully!")
        print("💡 Tips:")
        print("   - Restart your Flask app if it's running")
        print("   - Clear browser cache/cookies if login still fails")
        print("   - Use the exact password from your .env file")
    else:
        print("\n❌ Password reset failed!")
        print("💡 Troubleshooting:")
        print("   - Check if .env file exists and contains ADMIN_PASSWORD")
        print("   - Verify database file (ai_learning.db) exists")
        print("   - Make sure you have write permissions")

if __name__ == "__main__":
    main()
