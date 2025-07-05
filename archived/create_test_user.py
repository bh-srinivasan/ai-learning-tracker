#!/usr/bin/env python3
"""
Create a test user to monitor for deletion
"""
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_test_user():
    """Create a test user named Sachin to monitor deletion"""
    db_path = 'ai_learning.db'
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check if Sachin already exists
        existing = conn.execute("SELECT id FROM users WHERE username = 'Sachin'").fetchone()
        if existing:
            print(f"✅ Test user 'Sachin' already exists (ID: {existing['id']})")
            return
        
        # Create test user
        password_hash = generate_password_hash('sachin123')
        
        cursor = conn.execute("""
            INSERT INTO users (username, password_hash, level, user_selected_level, status)
            VALUES (?, ?, ?, ?, ?)
        """, ('Sachin', password_hash, 'Beginner', 'Beginner', 'active'))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Created test user 'Sachin' with ID: {user_id}")
        print(f"   Username: Sachin")
        print(f"   Password: sachin123")
        print(f"   Created at: {datetime.now()}")
        
        # Verify creation
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            print(f"✅ Verification successful - user created with timestamp: {user['created_at']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")

if __name__ == "__main__":
    create_test_user()
