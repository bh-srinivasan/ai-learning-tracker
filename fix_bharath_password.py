#!/usr/bin/env python3
"""
Reset bharath password to 'bharath' (as intended for testing)
"""

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def fix_bharath_password():
    conn = sqlite3.connect('ai_learning.db')
    
    # Reset bharath's password to 'bharath' for testing
    bharath_hash = generate_password_hash('bharath')
    
    # Update bharath's password
    conn.execute(
        'UPDATE users SET password_hash = ? WHERE username = ?',
        (bharath_hash, 'bharath')
    )
    conn.commit()
    
    print("✅ bharath password reset to 'bharath' for testing")
    
    # Verify the update
    user = conn.execute(
        'SELECT password_hash FROM users WHERE username = ?',
        ('bharath',)
    ).fetchone()
    
    if user and check_password_hash(user[0], 'bharath'):
        print("✅ Password verification successful")
    else:
        print("❌ Password verification failed")
    
    conn.close()

if __name__ == "__main__":
    fix_bharath_password()
