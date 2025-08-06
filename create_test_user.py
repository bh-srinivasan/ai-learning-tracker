#!/usr/bin/env python3
"""Create a regular user for testing"""

import sqlite3
import hashlib
import uuid
from datetime import datetime

def create_test_user():
    """Create a regular test user"""
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Check if test user already exists
        test_user = conn.execute(
            'SELECT id FROM users WHERE username = ?',
            ('testuser',)
        ).fetchone()
        
        if test_user:
            print("Test user already exists!")
            return
        
        # Create test user
        username = 'testuser'
        password = 'test123'  # Simple password for testing
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn.execute('''
            INSERT INTO users (username, password_hash, created_at, level, points, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, datetime.now(), 'Learner', 150, 'active'))
        
        conn.commit()
        print(f"Test user created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Level: Learner (150 points)")
        print(f"URL: http://127.0.0.1:5000/login")
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_test_user()
