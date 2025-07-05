#!/usr/bin/env python3
"""
Monitor database changes to detect when users are deleted
"""
import sqlite3
import os
import time
import hashlib
from datetime import datetime

def get_db_hash():
    """Get a hash of the database to detect changes"""
    db_path = 'ai_learning.db'
    if not os.path.exists(db_path):
        return None
    
    with open(db_path, 'rb') as f:
        content = f.read()
        return hashlib.md5(content).hexdigest()

def get_user_count():
    """Get the current user count"""
    db_path = 'ai_learning.db'
    if not os.path.exists(db_path):
        return 0
    
    try:
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def check_test_user():
    """Check if our test user Sachin still exists"""
    db_path = 'ai_learning.db'
    if not os.path.exists(db_path):
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        user = conn.execute("SELECT id FROM users WHERE username = 'Sachin'").fetchone()
        conn.close()
        return user is not None
    except:
        return False

def monitor_database():
    """Monitor database for changes that might indicate user deletion"""
    print("🔍 DATABASE MONITORING STARTED")
    print("=" * 50)
    print("Monitoring for user deletions and database changes...")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    last_hash = get_db_hash()
    last_user_count = get_user_count()
    last_test_user_exists = check_test_user()
    
    print(f"Initial state:")
    print(f"  Database hash: {last_hash[:8]}...")
    print(f"  User count: {last_user_count}")
    print(f"  Test user 'Sachin' exists: {last_test_user_exists}")
    print()
    
    try:
        while True:
            time.sleep(10)  # Check every 10 seconds
            
            current_hash = get_db_hash()
            current_user_count = get_user_count()
            current_test_user_exists = check_test_user()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Check for changes
            if current_hash != last_hash:
                print(f"[{timestamp}] 🚨 DATABASE FILE CHANGED!")
                print(f"              Previous hash: {last_hash[:8] if last_hash else 'None'}...")
                print(f"              Current hash:  {current_hash[:8] if current_hash else 'None'}...")
                
                if current_user_count != last_user_count:
                    print(f"              User count changed: {last_user_count} → {current_user_count}")
                    if current_user_count < last_user_count:
                        print(f"              ⚠️  USERS DELETED: {last_user_count - current_user_count} users lost!")
                    elif current_user_count > last_user_count:
                        print(f"              ✅ USERS ADDED: {current_user_count - last_user_count} new users")
                
                if current_test_user_exists != last_test_user_exists:
                    if not current_test_user_exists:
                        print(f"              🚨 TEST USER 'Sachin' WAS DELETED!")
                    else:
                        print(f"              ✅ TEST USER 'Sachin' WAS RESTORED!")
                
                # Update tracking variables
                last_hash = current_hash
                last_user_count = current_user_count
                last_test_user_exists = current_test_user_exists
                print()
            
            # Print periodic status
            if int(time.time()) % 60 == 0:  # Every minute
                print(f"[{timestamp}] Status: {current_user_count} users, Test user: {'✅' if current_test_user_exists else '❌'}")
    
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        
        # Final status check
        final_hash = get_db_hash()
        final_user_count = get_user_count()
        final_test_user_exists = check_test_user()
        
        print("\n📊 FINAL STATUS:")
        print(f"  Database hash: {final_hash[:8] if final_hash else 'None'}...")
        print(f"  User count: {final_user_count}")
        print(f"  Test user 'Sachin' exists: {final_test_user_exists}")
        
        if not final_test_user_exists:
            print("\n🚨 CONCLUSION: Test user was deleted during monitoring!")
            print("   This confirms the user deletion issue exists.")
        else:
            print("\n✅ CONCLUSION: Test user survived monitoring period.")
            print("   User deletion issue may be intermittent or trigger-based.")

if __name__ == "__main__":
    monitor_database()
