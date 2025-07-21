#!/usr/bin/env python3
"""
Test admin login to ensure credentials work
"""
import sqlite3
import os
from werkzeug.security import check_password_hash

def test_admin_login():
    """Test admin credentials"""
    
    # Get admin password from environment
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    print(f"🔑 Testing with admin password from environment")
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get admin user
    cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", ('admin',))
    admin_user = cursor.fetchone()
    
    if not admin_user:
        print("❌ Admin user not found in database!")
        conn.close()
        return False
    
    print(f"✅ Admin user found: {admin_user['username']}")
    
    # Test password
    if check_password_hash(admin_user['password_hash'], admin_password):
        print("✅ Admin password is correct!")
        print("🎉 Admin login should work fine")
        conn.close()
        return True
    else:
        print("❌ Admin password is incorrect!")
        print("🔧 Need to reset admin password")
        conn.close()
        return False

if __name__ == "__main__":
    success = test_admin_login()
    if not success:
        print("\n🚨 ADMIN LOGIN ISSUE DETECTED")
        print("Run this to fix: python app.py (it will reset admin password)")
