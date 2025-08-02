#!/usr/bin/env python3
"""
Direct admin creation script for Azure
This script creates an admin user directly via HTTP request simulation
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user_directly():
    """Create admin user directly in the database"""
    try:
        # Try to connect to the database
        db_path = 'ai_learning.db'  # This will be the path in Azure too
        
        print(f"🔄 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create users table if it doesn't exist
        print("🔧 Creating users table if not exists...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                user_selected_level TEXT DEFAULT 'Beginner',
                login_count INTEGER DEFAULT 0
            )
        ''')
        
        # Check if admin already exists
        print("🔍 Checking if admin user exists...")
        existing_admin = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if existing_admin:
            print(f"✅ Admin user already exists with ID: {existing_admin['id']}")
            conn.close()
            return True
        
        # Create admin user
        print("👤 Creating admin user...")
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 100, 'active', 'Advanced', 0, datetime.now().isoformat()))
        
        conn.commit()
        admin_id = conn.lastrowid
        conn.close()
        
        print(f"✅ Admin user created successfully!")
        print(f"   Admin ID: {admin_id}")
        print(f"   Username: admin")
        print(f"   Password: YourSecureAdminPassword123!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin: {str(e)}")
        return False

def verify_admin_creation():
    """Verify the admin user was created correctly"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        if admin:
            print(f"✅ Verification successful:")
            print(f"   ID: {admin['id']}")
            print(f"   Username: {admin['username']}")
            print(f"   Level: {admin['level']}")
            print(f"   Points: {admin['points']}")
            print(f"   Created: {admin['created_at']}")
        else:
            print("❌ Admin user not found after creation")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification error: {e}")

if __name__ == '__main__':
    print("🚀 Direct Admin Creation Script")
    print("=" * 40)
    
    if create_admin_user_directly():
        print("\n🔍 Verifying creation...")
        verify_admin_creation()
        print("\n✅ Admin creation completed successfully!")
        print("You can now test login with:")
        print("   Username: admin")
        print("   Password: YourSecureAdminPassword123!")
    else:
        print("\n❌ Admin creation failed!")
