#!/usr/bin/env python3
"""Test admin password verification"""

import sqlite3
from werkzeug.security import check_password_hash

def test_admin_password():
    print("🔍 Testing admin password verification...")
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get admin user
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if not admin_user:
        print("❌ Admin user not found!")
        return
    
    print(f"✅ Admin user found: ID={admin_user['id']}")
    print(f"   Password hash: {admin_user['password_hash'][:50]}...")
    
    # Test common passwords
    test_passwords = [
        'YourSecureAdminPassword123!',
        'admin',
        'password',
        'admin123',
        'YourSecureAdminPasswordForProduction123!',
        'default_admin_password'
    ]
    
    for password in test_passwords:
        is_valid = check_password_hash(admin_user['password_hash'], password)
        status = "✅" if is_valid else "❌"
        print(f"   {status} Password '{password}': {'VALID' if is_valid else 'INVALID'}")
        
        if is_valid:
            print(f"🎉 CORRECT PASSWORD FOUND: '{password}'")
            break
    
    conn.close()

if __name__ == "__main__":
    test_admin_password()
