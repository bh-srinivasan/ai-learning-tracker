#!/usr/bin/env python3
"""
Database investigation script with environment detection
Automatically detects LOCAL vs AZURE and analyzes appropriately
"""
import sqlite3
import os
import platform
from datetime import datetime

def detect_environment():
    """Detect if running locally or on Azure"""
    azure_indicators = [
        'WEBSITE_SITE_NAME',
        'WEBSITE_RESOURCE_GROUP',
        'SCM_REPOSITORY_PATH',
    ]
    
    for indicator in azure_indicators:
        if os.getenv(indicator):
            return 'AZURE'
            
    return 'LOCAL'

def check_database():
    env = detect_environment()
    db_path = 'ai_learning.db'
    
    print(f"🌍 ENVIRONMENT: {env}")
    print(f"🖥️  Platform: {platform.platform()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        if env == 'AZURE':
            print("🚨 CRITICAL: On Azure, this means database gets recreated on each deployment!")
            print("   This explains why users keep getting deleted!")
        return
    
    print(f"✅ Database file {db_path} exists. Size: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check users table schema
        print("\n=== USERS TABLE SCHEMA ===")
        schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        if schema:
            print(schema['sql'])
        else:
            print("Users table not found!")
            return
        
        # Check current users
        print("\n=== CURRENT USERS ===")
        users = conn.execute("SELECT id, username, password_hash, created_at, last_login, last_activity FROM users").fetchall()
        for user in users:
            print(f"ID: {user['id']}, Username: {user['username']}")
            print(f"  Password Hash: {user['password_hash'][:20]}... (truncated)")
            print(f"  Created: {user['created_at']}")
            print(f"  Last Login: {user['last_login']}")
            print(f"  Last Activity: {user['last_activity']}")
            print()
        
        # Check if there are any triggers or other automation
        print("=== DATABASE TRIGGERS ===")
        triggers = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall()
        if triggers:
            for trigger in triggers:
                print(f"Trigger: {trigger['name']}")
                print(f"SQL: {trigger['sql']}")
                print()
        else:
            print("No triggers found")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")

def investigate_user_deletion():
    """Investigate why users are being deleted after server refresh"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    print("\n🔍 INVESTIGATING USER DELETION ISSUE")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check all current users
        print("1. CURRENT USER COUNT AND DATA")
        print("-" * 40)
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        print(f"Total users in database: {len(users)}")
        
        for user in users:
            print(f"  ID: {user['id']} | Username: {user['username']} | Created: {user['created_at']}")
        
        # Check for any database recreation patterns
        print("\n2. DATABASE FILE INFORMATION")
        print("-" * 40)
        db_stat = os.stat(db_path)
        db_size = db_stat.st_size
        db_modified = datetime.fromtimestamp(db_stat.st_mtime)
        db_created = datetime.fromtimestamp(db_stat.st_ctime)
        
        print(f"Database size: {db_size} bytes")
        print(f"Last modified: {db_modified}")
        print(f"Created: {db_created}")
        
        # Check if database is being recreated recently
        now = datetime.now()
        time_since_modified = now - db_modified
        time_since_created = now - db_created
        
        if time_since_modified.total_seconds() < 3600:  # Modified in last hour
            print("⚠️  WARNING: Database was modified recently (within last hour)")
            print("   This could indicate automatic recreation/seeding")
        
        if time_since_created.total_seconds() < 3600:  # Created in last hour
            print("🚨 CRITICAL: Database was created recently (within last hour)")
            print("   This strongly suggests the database is being recreated on startup!")
        
        # Check for specific test users
        print("\n3. CHECKING FOR TEST USERS")
        print("-" * 40)
        test_users = ['sachin', 'Sachin', 'demo', 'test']
        found_test_users = []
        
        for test_user in test_users:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (test_user,)).fetchone()
            if user:
                found_test_users.append(test_user)
                print(f"✅ Found test user: {test_user} (ID: {user['id']}, Created: {user['created_at']})")
            else:
                print(f"❌ Missing test user: {test_user}")
        
        if not found_test_users:
            print("🚨 NO TEST USERS FOUND - This confirms users are being deleted!")
        
        # Check for any foreign key constraints that might cascade deletes
        print("\n4. CHECKING DATABASE CONSTRAINTS")
        print("-" * 40)
        
        foreign_keys = conn.execute("PRAGMA foreign_key_list(users)").fetchall()
        if foreign_keys:
            print("Foreign key constraints on users table:")
            for fk in foreign_keys:
                print(f"  {fk}")
        else:
            print("No foreign key constraints on users table")
        
        # Check indexes
        indexes = conn.execute("PRAGMA index_list(users)").fetchall()
        if indexes:
            print("Indexes on users table:")
            for idx in indexes:
                print(f"  {idx}")
        
        # Check for any triggers that might delete users
        triggers = conn.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='trigger' AND (sql LIKE '%DELETE%' OR sql LIKE '%users%')
        """).fetchall()
        
        if triggers:
            print("\n5. SUSPICIOUS TRIGGERS (that might delete users)")
            print("-" * 40)
            for trigger in triggers:
                print(f"Trigger: {trigger['name']}")
                print(f"SQL: {trigger['sql']}")
                print()
        else:
            print("\n5. No triggers found that delete users")
        
        conn.close()
        
        print("\n6. CHECKING FOR DATABASE SEEDING/INITIALIZATION")
        print("-" * 40)
        
        # Look for files that might be recreating the database
        suspicious_files = [
            'app.py',
            'startup.py', 
            'init_db.py',
            'seed.py',
            'migrate.py',
            'reset_db.py'
        ]
        
        for file_name in suspicious_files:
            if os.path.exists(file_name):
                print(f"📁 Found: {file_name} - checking for database recreation...")
                
    except Exception as e:
        print(f"Error during investigation: {e}")

def check_safe_init_db_function():
    """Check if safe_init_db function is working properly"""
    print("\n7. ANALYZING SAFE_INIT_DB FUNCTION")
    print("-" * 40)
    
    try:
        # Import and check safe_init_db function
        import sys
        sys.path.insert(0, '.')
        
        from app import safe_init_db
        import inspect
        
        # Get the source code of safe_init_db
        source = inspect.getsource(safe_init_db)
        
        # Check for safe patterns
        safe_patterns = [
            'os.path.exists',
            'if not os.path.exists',
            'DATABASE already exists',
        ]
        
        print("Checking safe_init_db function for safety patterns:")
        for pattern in safe_patterns:
            if pattern in source:
                print(f"✅ FOUND SAFE PATTERN: {pattern}")
                print("   This helps prevent data loss!")
            else:
                print(f"⚠️  Pattern not found: '{pattern}'")
        
        # Check if it properly protects existing data
        if 'DATABASE already exists' in source:
            print("✅ Good: Checks if database exists before initialization")
        else:
            print("⚠️  Warning: May not check for existing database")
        
    except Exception as e:
        print(f"Error analyzing safe_init_db: {e}")

if __name__ == "__main__":
    check_database()
    investigate_user_deletion()
    check_safe_init_db_function()
