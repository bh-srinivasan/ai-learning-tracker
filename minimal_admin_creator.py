#!/usr/bin/env python3
"""
Minimal Admin Creator
=====================
Minimal script to create admin user - copy this into Kudu console
"""

# Run this in the Azure console:
# python -c "exec(open('minimal_admin_creator.py').read())"

import sqlite3
import hashlib
import secrets
from datetime import datetime

def create_admin_user():
    try:
        # Connect to database
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            print("✅ Admin user already exists")
            conn.close()
            return True
        
        # Create password hash (simplified)
        password = "YourSecureAdminPassword1223!"  # Replace with your actual password
        
        # Simple password hashing (for emergency use)
        import hashlib
        password_hash = "pbkdf2:sha256:260000$" + hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 260000).hex()
        
        # Create admin user
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print("🎉 Admin user created successfully!")
        print("Username: admin")
        print("Password: YourSecureAdminPassword1223!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_admin_user()
