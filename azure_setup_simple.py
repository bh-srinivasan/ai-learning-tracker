#!/usr/bin/env python3
"""
Azure Simple Setup - Single Command Solution
===========================================
Run this once in Azure to set up admin user.

Usage in Azure Console:
python azure_setup_simple.py
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Get admin password from environment or use default
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')

def setup_admin():
    """One-function admin setup"""
    print("🚀 Setting up admin user...")
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute('SELECT id FROM users WHERE username = "admin"')
        if cursor.fetchone():
            print('✅ Admin already exists - no action needed')
            return
        
        # Create admin
        password_hash = generate_password_hash(ADMIN_PASSWORD)
        cursor.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 1000, 'active', 'Advanced', 0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print('🎉 Admin user created!')
        print(f'   Username: admin')
        print(f'   Password: {ADMIN_PASSWORD}')
        print('✅ Setup complete!')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    setup_admin()
