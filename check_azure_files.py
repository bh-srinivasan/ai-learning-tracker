#!/usr/bin/env python3
"""
Complete Azure Admin Setup
===========================
Run this script in Azure environment to set up admin user.
"""

import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def check_azure_files():
    """Check if required files exist"""
    
    print("=== AZURE ENVIRONMENT VERIFICATION ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print()
    
    # Check for key files
    key_files = ['app.py', 'ai_learning.db', 'requirements.txt']
    
    print("📁 Key files status:")
    for file in key_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} - Found ({size} bytes)")
        else:
            print(f"❌ {file} - Missing")
    
    print()
    print("📂 Directory contents (first 15 files):")
    try:
        files = sorted(os.listdir('.'))[:15]
        for f in files:
            print(f"   {f}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("🔍 Environment check:")
    azure_env = os.environ.get('WEBSITE_SITE_NAME')
    if azure_env:
        print(f"✅ Azure App Service detected: {azure_env}")
    else:
        print("❌ Not in Azure environment")
    
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    if admin_pwd:
        print(f"✅ ADMIN_PASSWORD configured (length: {len(admin_pwd)})")
    else:
        print("⚠️ ADMIN_PASSWORD not found, using default")

def create_admin_user_secure():
    """Create admin user with secure setup"""
    
    print("\n=== ADMIN USER INITIALIZATION ===")
    
    try:
        # Connect to database
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        print("✅ Database connection successful")
        
        # Check if admin exists
        cursor.execute('SELECT id, username, level FROM users WHERE username = "admin"')
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"✅ Admin user already exists:")
            print(f"   ID: {existing_admin[0]}")
            print(f"   Username: {existing_admin[1]}")
            print(f"   Level: {existing_admin[2]}")
            print("🔧 No action needed")
            conn.close()
            return True
        
        # Create admin user
        print("🚀 Creating admin user...")
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute('''
            INSERT INTO users (
                username, password_hash, level, points, status, 
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'admin', 
            password_hash, 
            'Advanced',     # Admin level
            1000,          # Admin points
            'active', 
            'Advanced', 
            0, 
            datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print("🎉 ADMIN USER CREATED SUCCESSFULLY!")
        print(f"   User ID: {admin_id}")
        print(f"   Username: admin")
        print(f"   Level: Advanced (Admin)")
        print(f"   Password: {admin_password}")
        print(f"   Points: 1000")
        print(f"   Status: Active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def main():
    """Main execution function"""
    
    print("🚀 AI Learning Tracker - Complete Azure Setup")
    print("=" * 60)
    
    # Check environment
    check_azure_files()
    
    # Create admin user
    success = create_admin_user_secure()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SETUP COMPLETE!")
        print("✅ Admin user is ready for login")
        print("\n🔗 Login URL: https://ai-learning-tracker-bharath.azurewebsites.net/")
        print("👤 Username: admin")
        print("🔑 Password: [check output above]")
    else:
        print("❌ Setup failed - check error messages above")
    print("=" * 60)

if __name__ == "__main__":
    main()
