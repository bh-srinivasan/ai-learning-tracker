#!/usr/bin/env python3
"""
Azure Admin User Initializer
============================

One-time script to create admin user in Azure database.
Safe to run multiple times - will not duplicate users.
"""

import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    """Create admin user if it doesn't exist"""
    print("=== AZURE ADMIN USER INITIALIZER ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database configuration
    db_path = 'ai_learning.db'
    
    # Get admin password from environment
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        admin_password = 'YourSecureAdminPassword1223!'  # Fallback
        print("⚠️ Using fallback admin password")
    else:
        print("✅ Using admin password from environment variable")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"✅ Admin user already exists (ID: {existing_admin[0]})")
            print("🔧 No action needed - admin user is ready")
            conn.close()
            return True
        
        # Create admin user
        print("🚀 Creating admin user...")
        
        password_hash = generate_password_hash(admin_password)
        
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
            'admin',
            password_hash,
            'Advanced',  # Set admin as Advanced user
            100,         # Give admin some initial points
            'active',
            'Advanced',
            0,
            datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        
        # Commit the changes
        conn.commit()
        
        print(f"✅ Admin user created successfully!")
        print(f"   User ID: {admin_id}")
        print(f"   Username: admin")
        print(f"   Level: Advanced")
        print(f"   Status: active")
        print(f"   Password: {'*' * len(admin_password)} (from environment)")
        
        # Verify the user was created
        cursor.execute("SELECT id, username, level, status FROM users WHERE username = 'admin'")
        verification = cursor.fetchone()
        
        if verification:
            print("✅ Admin user verification PASSED")
        else:
            print("❌ Admin user verification FAILED")
            conn.close()
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def create_demo_user():
    """Create demo user for testing"""
    print("\n=== CREATING DEMO USER ===")
    
    db_path = 'ai_learning.db'
    demo_password = os.environ.get('DEMO_PASSWORD', 'demo123')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if demo user exists
        cursor.execute("SELECT id FROM users WHERE username = 'demo'")
        if cursor.fetchone():
            print("✅ Demo user already exists")
            conn.close()
            return True
        
        # Create demo user
        password_hash = generate_password_hash(demo_password)
        
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
            'demo',
            password_hash,
            'Beginner',
            0,
            'active',
            'Beginner',
            0,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Demo user created (password: {demo_password})")
        return True
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
        return False

def verify_database_tables():
    """Verify that required tables exist"""
    print("\n=== DATABASE VERIFICATION ===")
    
    db_path = 'ai_learning.db'
    required_tables = ['users', 'courses', 'learning_entries']
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check each required table
        all_tables_exist = True
        for table in required_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                all_tables_exist = False
        
        # Get total user count
        if all_tables_exist:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"📊 Total users in database: {user_count}")
        
        conn.close()
        return all_tables_exist
        
    except Exception as e:
        print(f"❌ Database verification error: {e}")
        return False

def main():
    """Main initialization function"""
    print("AI Learning Tracker - Azure Admin User Initializer")
    print("=" * 60)
    
    # Check database tables first
    if not verify_database_tables():
        print("\n❌ Database tables missing - initialization required")
        print("🔧 Run database initialization first")
        return False
    
    # Create admin user
    admin_success = create_admin_user()
    
    # Create demo user
    demo_success = create_demo_user()
    
    print("\n" + "=" * 60)
    print("INITIALIZATION SUMMARY:")
    print(f"Admin user: {'✅ SUCCESS' if admin_success else '❌ FAILED'}")
    print(f"Demo user:  {'✅ SUCCESS' if demo_success else '❌ FAILED'}")
    
    if admin_success:
        print("\n🎉 Azure database is ready!")
        print("🔗 You can now login to your application:")
        print("   URL: https://ai-learning-tracker-bharath.azurewebsites.net/")
        print("   Username: admin")
        print("   Password: [from environment variable]")
    else:
        print("\n❌ Initialization failed - check logs above")
    
    return admin_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
