#!/usr/bin/env python3
"""
Admin User Verification
=======================

Check admin user status and verify password functionality.
"""

import sqlite3
import os
from werkzeug.security import check_password_hash

def check_admin_user():
    """Check admin user in database"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get admin user details
        cursor.execute("SELECT username, password_hash, level, points, status, last_login, login_count FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        print("=== ADMIN USER STATUS ===")
        if not admin:
            print("❌ Admin user not found in database")
            return False
        
        username, password_hash, level, points, status, last_login, login_count = admin
        
        print(f"✅ Admin user found:")
        print(f"   Username: {username}")
        print(f"   Level: {level}")
        print(f"   Points: {points}")
        print(f"   Status: {status}")
        print(f"   Last Login: {last_login}")
        print(f"   Login Count: {login_count}")
        print(f"   Password Hash: {password_hash[:50]}...")
        
        # Test password verification
        print("\n=== PASSWORD VERIFICATION TEST ===")
        
        # Try common passwords
        test_passwords = []
        
        # Get password from environment if available
        env_password = os.environ.get('ADMIN_PASSWORD')
        if env_password:
            test_passwords.append(('Environment Variable', env_password))
        
        # Common test passwords
        test_passwords.extend([
            ('Default', 'admin'),
            ('Common', 'password'),
            ('Common', 'admin123'),
            ('Environment fallback', 'Password123')
        ])
        
        password_found = False
        for desc, test_pwd in test_passwords:
            if check_password_hash(password_hash, test_pwd):
                print(f"✅ Password verification SUCCESS with {desc}: '{test_pwd}'")
                password_found = True
                break
            else:
                print(f"❌ Password verification FAILED with {desc}: '{test_pwd}'")
        
        if not password_found:
            print("\n⚠️ No password matched. Admin login will fail.")
            print("🔧 You may need to reset the admin password.")
        
        conn.close()
        return password_found
        
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")
        return False

def check_all_users():
    """Check all users for debugging"""
    db_path = 'ai_learning.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, level, points, status, login_count FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print(f"\n=== ALL USERS ({len(users)} total) ===")
        for user in users:
            user_id, username, level, points, status, login_count = user
            print(f"ID {user_id:2}: {username:15} | {level:10} | {points:3} pts | {status:8} | {login_count:3} logins")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")

if __name__ == "__main__":
    print("AI Learning Tracker - Admin User Verification")
    print("=" * 50)
    
    admin_ok = check_admin_user()
    check_all_users()
    
    print("\n" + "=" * 50)
    if admin_ok:
        print("✅ Admin user verification PASSED")
    else:
        print("❌ Admin user verification FAILED")
        print("🔧 Check environment variables or reset admin password")
