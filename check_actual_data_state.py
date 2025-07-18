#!/usr/bin/env python3
"""
Check the actual current state of user data
"""
import sqlite3
import os
from werkzeug.security import check_password_hash

def check_current_user_data():
    """Check what's actually in the database right now"""
    print("🔍 CHECKING ACTUAL CURRENT USER DATA STATE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute('SELECT username, password_hash, created_at, status FROM users ORDER BY username')
        users = cursor.fetchall()
        
        if not users:
            print("❌ No users found in database")
            return
            
        print(f"Found {len(users)} users:")
        print()
        
        for username, pwd_hash, created, status in users:
            print(f"User: {username}")
            print(f"  Status: {status}")
            print(f"  Created: {created}")
            print(f"  Password hash length: {len(pwd_hash) if pwd_hash else 0}")
            print(f"  Hash starts with: {pwd_hash[:30] if pwd_hash else 'None'}...")
            
            # Test common passwords that I might have set
            possible_passwords = [
                username,  # original intended password
                f"{username}_reset123",  # the format I used
                "admin",   # if I hardcoded admin
                "demo",    # if I hardcoded demo
                "bharath", # if I hardcoded bharath
            ]
            
            print(f"  Testing if password was changed to predictable formats:")
            for test_pwd in possible_passwords:
                try:
                    if check_password_hash(pwd_hash, test_pwd):
                        if test_pwd == username:
                            print(f"    ✅ Password is original: '{test_pwd}'")
                        else:
                            print(f"    🚨 PASSWORD WAS CHANGED TO: '{test_pwd}'")
                except:
                    pass
            print()
            
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_current_user_data()
