#!/usr/bin/env python3
"""
Reset admin password to fix login issue
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset admin password"""
    
    # Get admin password from environment
    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    password_hash = generate_password_hash(admin_password)
    
    print(f"🔑 Resetting admin password...")
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Update admin password
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, 'admin'))
    rows_affected = cursor.rowcount
    
    if rows_affected > 0:
        conn.commit()
        print(f"✅ Admin password reset successfully")
        print(f"🔐 Username: admin")
        print(f"🔐 Password: {admin_password}")
    else:
        print(f"❌ Admin user not found!")
    
    conn.close()
    return rows_affected > 0

if __name__ == "__main__":
    success = reset_admin_password()
    if success:
        print("🎉 Admin login should work now!")
    else:
        print("❌ Failed to reset password")
