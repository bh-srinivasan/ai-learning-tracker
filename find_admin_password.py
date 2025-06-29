#!/usr/bin/env python3
"""
Script to find the current admin password by checking the database
"""
import sqlite3
from werkzeug.security import check_password_hash

def find_admin_password():
    """Find the current admin password by testing common passwords against the hash"""
    
    print("🔍 FINDING CURRENT ADMIN PASSWORD")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Get admin user
        admin_user = conn.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if not admin_user:
            print("❌ Admin user not found in database!")
            return None
        
        print(f"✅ Found admin user (ID: {admin_user['id']})")
        print(f"   Username: {admin_user['username']}")
        print(f"   Password Hash: {admin_user['password_hash'][:30]}...")
        
        # List of possible passwords to test
        possible_passwords = [
            'admin',                    # Original default
            'NewAdminPass123!',        # From password update tests
            'AdminPass123!',           # Variation
            'AdminPass123',            # Without special char
            'SecureAdmin123!',         # Another variation
            'admin123',                # Simple variation
            'password',                # Common default
            'Administrator',           # Common admin password
            'Admin123',                # Simple admin password
            'StrongAdminPass2024!',    # Strong password variation
            'TestAdmin123!',           # Test password
            'AdminPassword123!',       # Descriptive password
        ]
        
        print(f"\n🔑 Testing {len(possible_passwords)} possible passwords...")
        
        for i, password in enumerate(possible_passwords, 1):
            print(f"   {i:2d}. Testing '{password}'...", end=" ")
            
            if check_password_hash(admin_user['password_hash'], password):
                print("✅ MATCH!")
                print(f"\n🎉 FOUND ADMIN PASSWORD!")
                print(f"   Current admin password: '{password}'")
                return password
            else:
                print("❌")
        
        print(f"\n❌ None of the {len(possible_passwords)} tested passwords worked!")
        print("   The admin password may have been changed to something custom.")
        
        # Check if it's a recently generated secure password
        print("\n🔧 Checking if it might be a generated secure password...")
        print("   (These would be 12+ character random passwords)")
        
        hash_length = len(admin_user['password_hash'])
        print(f"   Password hash length: {hash_length} characters")
        
        if hash_length > 60:  # bcrypt hashes are typically 60 chars
            print("   ✅ Hash appears to be bcrypt format (secure)")
        else:
            print("   ⚠️  Hash format might be different")
        
        return None
        
    except Exception as e:
        print(f"❌ Error accessing database: {str(e)}")
        return None
        
    finally:
        conn.close()

def show_password_reset_options():
    """Show options for resetting the admin password if needed"""
    
    print("\n" + "=" * 50)
    print("🛠️  PASSWORD RESET OPTIONS")
    print("=" * 50)
    print()
    print("If the admin password is unknown, you can:")
    print()
    print("1. 🔄 Reset via Database (Direct):")
    print("   - Directly update the password hash in the database")
    print("   - Use a known password like 'admin' for testing")
    print()
    print("2. 🔄 Reset via Application:")
    print("   - Use the admin password change feature")
    print("   - Access via /admin/change-password")
    print()
    print("3. 🔄 Reset to Default:")
    print("   - Set password back to 'admin' for consistency")
    print("   - Update all test scripts accordingly")
    print()
    print("Would you like me to:")
    print("   A) Reset the password to 'admin'")
    print("   B) Set a new secure password")
    print("   C) Show the current hash for manual inspection")

if __name__ == "__main__":
    found_password = find_admin_password()
    
    if not found_password:
        show_password_reset_options()
    else:
        print(f"\n🚀 SUCCESS!")
        print(f"   Admin password is: '{found_password}'")
        print(f"   You can now use this password to login.")
        print(f"   Update your test scripts to use this password.")
