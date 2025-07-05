#!/usr/bin/env python3
"""
Test Login Credentials
Verify that the admin and demo user credentials work correctly
"""

import os
import sqlite3
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

def test_user_login(username, password):
    """Test if user can login with given credentials"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Get user from database
        cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User '{username}' not found in database")
            return False
        
        # Check password
        if check_password_hash(user[1], password):
            print(f"✅ Login successful for '{username}'")
            return True
        else:
            print(f"❌ Password incorrect for '{username}'")
            return False
            
    except Exception as e:
        print(f"❌ Error testing login for '{username}': {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Test admin and demo user logins (excluding protected users)"""
    print("🔐 Testing Login Credentials")
    print("=" * 30)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    admin_password = os.environ.get('ADMIN_PASSWORD')
    demo_username = os.environ.get('DEMO_USERNAME', 'demo')
    demo_password = os.environ.get('DEMO_PASSWORD')
    
    if not admin_password or not demo_password:
        print("❌ Environment variables not loaded properly")
        return
    
    print("🧪 Testing Admin Login...")
    admin_success = test_user_login('admin', admin_password)
    
    print(f"\n🧪 Testing Demo User Login ({demo_username})...")
    demo_success = test_user_login(demo_username, demo_password)
    
    print(f"\n🛡️  Protected User 'bharath' - skipped from testing")
    
    print("\n" + "=" * 30)
    print("📊 Test Results:")
    print(f"   Admin Login: {'✅ PASS' if admin_success else '❌ FAIL'}")
    print(f"   Demo Login:  {'✅ PASS' if demo_success else '❌ FAIL'}")
    print(f"   Protected:   🛡️  SKIPPED (bharath)")
    
    if admin_success and demo_success:
        print("\n🎉 All login tests passed!")
        print("🌐 You can now login at: http://localhost:5000")
        print("\n🔑 Test Login Credentials:")
        print(f"   Admin: admin / {admin_password}")
        print(f"   Demo:  {demo_username} / {demo_password}")
        print(f"   Protected: bharath / [use original password]")
    else:
        print("\n⚠️  Some login tests failed!")
        print("💡 Try running the safe password reset script")

if __name__ == "__main__":
    main()
