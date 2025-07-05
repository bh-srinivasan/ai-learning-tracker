#!/usr/bin/env python3
"""
Check password hashes
"""

import sqlite3
from werkzeug.security import check_password_hash

def check_password_hashes():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    users = conn.execute('SELECT * FROM users WHERE username IN ("admin", "bharath")').fetchall()
    
    print("Password verification:")
    print("=" * 50)
    
    for user in users:
        print(f"\nUser: {user['username']}")
        print(f"Hash: {user['password_hash']}")
        
        # Test common passwords
        test_passwords = ['admin', 'bharath', 'password', 'test', '123456']
        
        for pwd in test_passwords:
            if check_password_hash(user['password_hash'], pwd):
                print(f"✓ Correct password: '{pwd}'")
                break
        else:
            print("✗ None of the test passwords work")
    
    conn.close()

if __name__ == "__main__":
    check_password_hashes()
