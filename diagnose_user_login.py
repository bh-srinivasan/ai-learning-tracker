#!/usr/bin/env python3
"""
Diagnostic script to check user login issues
"""
import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash

def diagnose_user_login():
    """Diagnose user login issues"""
    
    print("🔍 USER LOGIN DIAGNOSTIC")
    print("=" * 40)
    
    db_path = "ai_learning.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        print(f"📋 USERS IN DATABASE:")
        print(f"   Total users: {len(users)}")
        
        for user in users:
            print(f"\n   👤 User: {user['username']}")
            print(f"      ID: {user['id']}")
            print(f"      Status: {user.get('status', 'N/A')}")
            print(f"      Level: {user.get('level', 'N/A')}")
            print(f"      Created: {user.get('created_at', 'N/A')}")
            print(f"      Password Hash Length: {len(user['password_hash']) if user['password_hash'] else 0}")
            
            # Test password verification for common passwords
            test_passwords = [
                user['username'],  # Username as password
                f"{user['username']}_reset123",  # Reset format
                'password',
                'admin123',
                '123456'
            ]
            
            print(f"      🔐 Password Test Results:")
            for test_pwd in test_passwords:
                try:
                    if check_password_hash(user['password_hash'], test_pwd):
                        print(f"         ✅ Password '{test_pwd}' - WORKS")
                    else:
                        print(f"         ❌ Password '{test_pwd}' - Failed")
                except Exception as e:
                    print(f"         ⚠️  Password '{test_pwd}' - Error: {e}")
        
        # Check if there are any database issues
        print(f"\n🔧 DATABASE STRUCTURE CHECK:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print(f"   Users table columns: {[col[1] for col in columns]}")
        
        # Check for any constraint issues
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchall()
        if integrity[0][0] == 'ok':
            print(f"   ✅ Database integrity: OK")
        else:
            print(f"   ❌ Database integrity issues: {integrity}")
        
        conn.close()
        
        print(f"\n💡 LOGIN TROUBLESHOOTING TIPS:")
        print(f"   1. Try using the exact username and password shown above")
        print(f"   2. Check if user status is 'active' (inactive users can't login)")
        print(f"   3. Verify password hash is not empty")
        print(f"   4. For new users, try the reset password format: username_reset123")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_user_passwords():
    """Fix user passwords to a known format"""
    
    print(f"\n🔧 FIXING USER PASSWORDS")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect("ai_learning.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, username FROM users WHERE username != 'admin'")
        users = cursor.fetchall()
        
        for user in users:
            # Set password to username (for testing)
            new_password = user['username']
            password_hash = generate_password_hash(new_password)
            
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                         (password_hash, user['id']))
            print(f"   ✅ Fixed password for {user['username']} → Password: {new_password}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 PASSWORD FIX COMPLETE!")
        print(f"   All users can now login with their username as password")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing passwords: {e}")
        return False

if __name__ == "__main__":
    success = diagnose_user_login()
    
    if success:
        fix_choice = input("\n🔧 Would you like to fix user passwords? (y/n): ").lower()
        if fix_choice == 'y':
            fix_user_passwords()
    
    print(f"\n📝 Next steps:")
    print(f"   1. Try logging in with the passwords shown above")
    print(f"   2. If still failing, restart the Flask server")
    print(f"   3. Check browser console for any JavaScript errors")
