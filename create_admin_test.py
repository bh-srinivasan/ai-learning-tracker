#!/usr/bin/env python3
"""Quick script to create an admin user for testing"""

import sqlite3
import hashlib
import uuid
import os
from datetime import datetime

def create_admin_user():
    """Create an admin user for testing purposes"""
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Check if admin already exists
        admin = conn.execute(
            'SELECT id FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        username = 'admin'
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Get from environment or use default for testing
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_id = str(uuid.uuid4())
        
        conn.execute('''
            INSERT INTO users (id, username, password_hash, created_at, level, points)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, password_hash, datetime.now(), 'Expert', 1500))
        
        conn.commit()
        print(f"Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"URL: http://127.0.0.1:5000/admin")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_admin_user()
