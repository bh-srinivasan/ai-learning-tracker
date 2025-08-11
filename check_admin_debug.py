#!/usr/bin/env python3
import sqlite3

def check_admin_user():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if user:
        print(f"Admin user found:")
        print(f"  Username: {user['username']}")
        print(f"  ID: {user['id']}")
        
        # Check if is_admin column exists
        try:
            is_admin = user['is_admin']
            print(f"  Is Admin: {is_admin}")
        except IndexError:
            print(f"  Is Admin: Column not found")
        
        password_hash = user['password_hash'] if 'password_hash' in user.keys() else None
        print(f"  Has password: {'Yes' if password_hash else 'No'}")
    else:
        print("Admin user NOT found in database")
    
    conn.close()

if __name__ == "__main__":
    check_admin_user()
