#!/usr/bin/env python3
"""
Test script to verify user passwords and database state
"""
import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash

def test_local_database():
    """Test the local database to understand the password issue"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return
    
    print("🔍 Testing local database user passwords...")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get all users
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        print(f"📊 Found {len(users)} users in local database:")
        
        # Test common password combinations
        test_passwords = {
            'admin': 'admin',
            'bharath': 'bharath', 
            'demo': 'demo',
            'test': 'test'
        }
        
        for user in users:
            username = user['username']
            password_hash = user['password_hash']
            
            print(f"\n👤 User: {username}")
            print(f"   ID: {user['id']}")
            print(f"   Created: {user['created_at']}")
            print(f"   Hash: {password_hash[:30]}...")
            
            # Test if any of the common passwords work
            found_password = False
            for test_pass in ['admin', 'bharath', 'demo', 'test', username]:
                if check_password_hash(password_hash, test_pass):
                    print(f"   ✅ Password: {test_pass}")
                    found_password = True
                    break
            
            if not found_password:
                print(f"   ❌ Password: Unknown (doesn't match common passwords)")
                
                # Try to verify if this is a valid hash
                test_hash = generate_password_hash(username)
                if len(password_hash) == len(test_hash):
                    print(f"   ℹ️  Hash format looks valid")
                else:
                    print(f"   ⚠️  Hash format might be invalid")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing local database: {e}")
        return False

def simulate_azure_environment():
    """Simulate Azure environment variables and test password generation"""
    print("\n🌐 Simulating Azure environment...")
    print("=" * 60)
    
    # Common Azure environment variable patterns
    test_envs = [
        {},  # No env vars
        {'ADMIN_PASSWORD': 'admin', 'DEMO_PASSWORD': 'demo'},
        {'ADMIN_PASSWORD': 'bharath123', 'DEMO_PASSWORD': 'demo123'},
    ]
    
    for i, env_vars in enumerate(test_envs):
        print(f"\n🔬 Test case {i+1}: {env_vars if env_vars else 'Default values'}")
        
        # Simulate the password retrieval logic from app.py
        admin_password = env_vars.get('ADMIN_PASSWORD', 'admin')
        demo_password = env_vars.get('DEMO_PASSWORD', 'demo')
        
        admin_hash = generate_password_hash(admin_password)
        demo_hash = generate_password_hash(demo_password)
        
        print(f"   Admin password: '{admin_password}' -> Hash starts with: {admin_hash[:20]}...")
        print(f"   Demo password: '{demo_password}' -> Hash starts with: {demo_hash[:20]}...")
        
        # Verify the hashes work
        if check_password_hash(admin_hash, admin_password):
            print(f"   ✅ Admin hash verification: SUCCESS")
        else:
            print(f"   ❌ Admin hash verification: FAILED")
            
        if check_password_hash(demo_hash, demo_password):
            print(f"   ✅ Demo hash verification: SUCCESS")
        else:
            print(f"   ❌ Demo hash verification: FAILED")

def main():
    print("🔐 PASSWORD VERIFICATION TEST")
    print("=" * 60)
    
    local_success = test_local_database()
    simulate_azure_environment()
    
    print("\n" + "=" * 60)
    print("💡 DIAGNOSIS:")
    if local_success:
        print("✅ Local database is accessible and users exist")
        print("🤔 If Azure login fails, it might be due to:")
        print("   1. Environment variable differences")
        print("   2. Database not being properly copied to Azure")
        print("   3. Session management issues")
        print("   4. Password hash generation differences")
    else:
        print("❌ Issues with local database access")
    print("=" * 60)

if __name__ == "__main__":
    main()
