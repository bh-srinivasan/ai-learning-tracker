#!/usr/bin/env python3
"""
Reset bharath user password to 'bharath'
"""

import sqlite3
from werkzeug.security import generate_password_hash

def reset_bharath_password():
    conn = sqlite3.connect('ai_learning.db')
    
    # Generate new hash for 'bharath' password
    new_hash = generate_password_hash('bharath')
    
    # Update bharath's password
    conn.execute(
        'UPDATE users SET password_hash = ? WHERE username = ?',
        (new_hash, 'bharath')
    )
    conn.commit()
    
    print("✓ bharath password reset to 'bharath'")
    
    # Verify the update
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?',
        ('bharath',)
    ).fetchone()
    
    if user:
        from werkzeug.security import check_password_hash
        if check_password_hash(user[2], 'bharath'):  # password_hash is the 3rd column
            print("✓ Password verification successful")
        else:
            print("✗ Password verification failed")
    
    conn.close()

if __name__ == "__main__":
    reset_bharath_password()
