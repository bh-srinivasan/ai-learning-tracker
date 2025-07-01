#!/usr/bin/env python3
"""
Test if bharath's current password matches the DEMO_PASSWORD environment variable
"""
import sqlite3
import os
from werkzeug.security import check_password_hash

def test_bharath_password():
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    # Get the DEMO_PASSWORD from environment (simulating Azure environment)
    demo_password = "DemoUserPassword123!"  # This is what's set in Azure
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get bharath's password hash
        user = conn.execute("SELECT password_hash FROM users WHERE username = 'bharath'").fetchone()
        if user:
            password_hash = user['password_hash']
            
            # Test if current password matches DEMO_PASSWORD
            if check_password_hash(password_hash, demo_password):
                print("🔍 ANALYSIS RESULT:")
                print("❌ Bharath's password IS currently set to DEMO_PASSWORD")
                print(f"   Current password: {demo_password}")
                print("   This confirms the password is being reset to the Azure environment variable")
            else:
                print("🔍 ANALYSIS RESULT:")
                print("✅ Bharath's password is NOT set to DEMO_PASSWORD")
                print("   This means the password has been manually changed")
                
                # Test common passwords
                common_passwords = ['bharath', 'demo', 'password', 'admin']
                for pwd in common_passwords:
                    if check_password_hash(password_hash, pwd):
                        print(f"   Current password appears to be: {pwd}")
                        break
                else:
                    print("   Current password is a custom value")
        else:
            print("Bharath user not found!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error testing password: {e}")

if __name__ == "__main__":
    test_bharath_password()
