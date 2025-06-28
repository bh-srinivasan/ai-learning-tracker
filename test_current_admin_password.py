#!/usr/bin/env python3
"""
Test that the admin password reset worked correctly
"""
import sqlite3
from werkzeug.security import check_password_hash

def test_current_admin_password():
    """Test the current admin password"""
    
    print("🧪 TESTING CURRENT ADMIN PASSWORD")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        admin_user = conn.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        print(f"✅ Found admin user (ID: {admin_user['id']})")
        print(f"   Username: {admin_user['username']}")
        print(f"   Hash: {admin_user['password_hash'][:30]}...")
        
        # Test the new password
        test_password = "AdminSecure123!"
        print(f"\n🔑 Testing password: '{test_password}'")
        
        if check_password_hash(admin_user['password_hash'], test_password):
            print("✅ Password verification successful!")
            return True
        else:
            print("❌ Password verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_current_admin_password()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("   Admin password is correctly set to: AdminSecure123!")
        print("   You can now use this password for login and tests")
    else:
        print("\n❌ FAILED!")
        print("   Admin password verification failed")
