#!/usr/bin/env python3
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

def test_admin_password():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if user:
        print(f"Testing password for admin user...")
        print(f"  Username: {user['username']}")
        
        stored_hash = user['password_hash']
        test_passwords = ['admin123', 'admin', 'password', 'YourSecureAdminPassword123!']
        
        print(f"  Stored hash: {stored_hash[:50]}...")
        
        for test_pw in test_passwords:
            result = check_password_hash(stored_hash, test_pw)
            print(f"  Password '{test_pw}': {'✅ MATCH' if result else '❌ No match'}")
            
        # If none match, let's reset to a known password
        if not any(check_password_hash(stored_hash, pw) for pw in test_passwords):
            print("\n  No passwords matched. Setting new password 'admin123'...")
            new_hash = generate_password_hash('admin123')
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
            conn.commit()
            print("  Password updated to 'admin123'")
    else:
        print("Admin user not found")
    
    conn.close()

if __name__ == "__main__":
    test_admin_password()
