#!/usr/bin/env python3
"""
Verify current state of user data to check if passwords were changed
"""
import sqlite3
import os
from werkzeug.security import check_password_hash

def verify_user_data_state():
    """Check what's actually in the database right now"""
    print("🔍 VERIFYING CURRENT USER DATA STATE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if database exists and has tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Database tables found: {[t[0] for t in tables]}")
        
        if ('users',) not in tables:
            print("❌ Users table not found")
            conn.close()
            return
        
        # Get all users
        cursor.execute('SELECT username, password_hash, created_at, status FROM users ORDER BY username')
        users = cursor.fetchall()
        
        if not users:
            print("❌ No users found in database")
            conn.close()
            return
            
        print(f"\n✅ Found {len(users)} users:")
        print()
        
        for username, pwd_hash, created, status in users:
            print(f"👤 User: {username}")
            print(f"   Status: {status}")
            print(f"   Created: {created}")
            print(f"   Password hash length: {len(pwd_hash) if pwd_hash else 0}")
            
            if pwd_hash:
                # Test if password matches the username (original intended)
                if check_password_hash(pwd_hash, username):
                    print(f"   ✅ Password appears to be original: '{username}'")
                else:
                    # Test if it was changed to reset format
                    reset_format = f"{username}_reset123"
                    if check_password_hash(pwd_hash, reset_format):
                        print(f"   🚨 PASSWORD WAS CHANGED TO: '{reset_format}'")
                    else:
                        print(f"   ❓ Password is set to some other value (not original, not reset format)")
            else:
                print(f"   ❌ No password hash found")
            print()
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    verify_user_data_state()
