#!/usr/bin/env python3
"""
Admin User Initializer
======================

Standalone script to create admin user with secure password hashing.
Safe to run multiple times - checks if admin exists first.
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

def hash_password(password):
    """Securely hash password using PBKDF2"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    
    # Hash the password with salt using PBKDF2
    pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 salt.encode('utf-8'), 
                                 100000)  # 100,000 iterations
    
    # Return in werkzeug format for compatibility
    return f"pbkdf2:sha256:100000${salt}${pwdhash.hex()}"

def get_database_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def admin_user_exists():
    """Check if admin user already exists"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"✅ Admin user already exists (ID: {result['id']})")
            return True
        else:
            print("❌ Admin user does not exist")
            return False
            
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")
        conn.close()
        return False

def create_admin_user(username="admin", password=None):
    """
    Create admin user with elevated privileges
    
    Args:
        username (str): Admin username (default: 'admin')
        password (str): Admin password (if None, uses environment variable)
    
    Returns:
        bool: True if user created successfully, False otherwise
    """
    
    print("=" * 50)
    print("🔧 ADMIN USER INITIALIZER")
    print("=" * 50)
    
    # Check if admin already exists
    if admin_user_exists():
        print("🔧 No action needed - admin user is ready")
        return True
    
    # Get password from parameter or environment
    if password is None:
        password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    
    print(f"🚀 Creating admin user: {username}")
    print(f"📊 Password length: {len(password)} characters")
    
    # Hash password securely
    password_hash = hash_password(password)
    print("✅ Password hashed securely")
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create admin user with elevated privileges
        cursor.execute("""
            INSERT INTO users (
                username, 
                password_hash, 
                level, 
                points, 
                status,
                user_selected_level,
                login_count,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            password_hash,
            'Advanced',      # Admin level
            1000,           # Starting points for admin
            'active',       # Active status
            'Advanced',     # User selected level
            0,              # Login count
            datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"🎉 Admin user created successfully!")
        print(f"   User ID: {admin_id}")
        print(f"   Username: {username}")
        print(f"   Level: Advanced (Admin privileges)")
        print(f"   Status: Active")
        print(f"   Password: {'*' * len(password)}")
        
        # Verify creation
        if admin_user_exists():
            print("✅ Admin user verification PASSED")
            return True
        else:
            print("❌ Admin user verification FAILED")
            return False
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        conn.close()
        return False

def initialize_admin():
    """Main initialization function"""
    
    print("AI Learning Tracker - Admin User Initializer")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create admin user
    success = create_admin_user()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 INITIALIZATION COMPLETE!")
        print("✅ Admin user is ready for login")
        print("\n🔗 Login Details:")
        print("   URL: https://ai-learning-tracker-bharath.azurewebsites.net/")
        print("   Username: admin")
        print("   Password: [your ADMIN_PASSWORD]")
    else:
        print("❌ INITIALIZATION FAILED!")
        print("🔧 Please check the error messages above")
    
    print("=" * 50)
    return success

if __name__ == "__main__":
    initialize_admin()
