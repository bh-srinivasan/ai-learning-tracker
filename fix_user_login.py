#!/usr/bin/env python3
"""
Simple script to check users and fix login issues
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

def check_and_fix_users():
    """Check users and fix any issues"""
    
    print("Checking users and login issues...")
    
    if not os.path.exists("ai_learning.db"):
        print("Database not found!")
        return
    
    try:
        conn = sqlite3.connect("ai_learning.db")
        conn.row_factory = sqlite3.Row
        
        # Get all users
        users = conn.execute("SELECT * FROM users").fetchall()
        
        print(f"Found {len(users)} users:")
        
        for user in users:
            print(f"  - {user['username']} (ID: {user['id']}, Status: {user.get('status', 'N/A')})")
            
            # For non-admin users, set password to username for easy testing
            if user['username'] != 'admin':
                new_password = user['username']
                password_hash = generate_password_hash(new_password)
                
                conn.execute('UPDATE users SET password_hash = ?, status = ? WHERE id = ?', 
                           (password_hash, 'active', user['id']))
                print(f"    → Set password to: {new_password}")
        
        conn.commit()
        conn.close()
        
        print("\nUser login fix complete!")
        print("Now try logging in with:")
        print("  - admin: (use your admin password)")
        print("  - other users: use their username as password")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_and_fix_users()
