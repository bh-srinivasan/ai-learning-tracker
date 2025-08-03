#!/usr/bin/env python3
"""
Check Admin User in Azure Database
"""

from database_manager import get_db_connection

def check_admin_user():
    """Check if admin user exists and is properly configured in Azure"""
    print("🔍 Checking Admin User in Azure Database...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check admin user
        cursor.execute("""
            SELECT id, username, level, points, status, created_at, 
                   last_login, login_count
            FROM users 
            WHERE username = ?
        """, ('admin',))
        
        admin = cursor.fetchone()
        
        if admin:
            print("✅ Admin user found in Azure database:")
            print(f"   ID: {admin[0]}")
            print(f"   Username: {admin[1]}")
            print(f"   Level: {admin[2] or 'Not set'}")
            print(f"   Points: {admin[3] or 0}")
            print(f"   Status: {admin[4] or 'Active'}")
            print(f"   Created: {admin[5] or 'Not set'}")
            print(f"   Last Login: {admin[6] or 'Never'}")
            print(f"   Login Count: {admin[7] or 0}")
            
            # Check if admin can login (has password hash)
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", ('admin',))
            pwd_hash = cursor.fetchone()
            
            if pwd_hash and pwd_hash[0]:
                print("✅ Admin has password hash - can login")
            else:
                print("❌ Admin has no password hash - cannot login")
                
        else:
            print("❌ Admin user NOT FOUND in Azure database!")
            
        # Check all users for reference
        cursor.execute("SELECT id, username, status FROM users ORDER BY id")
        all_users = cursor.fetchall()
        
        print(f"\n📊 All users in Azure database ({len(all_users)} total):")
        for user in all_users:
            status_icon = "✅" if user[2] == "active" else "⚠️"
            print(f"   {status_icon} ID: {user[0]}, Username: {user[1]}, Status: {user[2] or 'active'}")
        
        conn.close()
        return admin is not None
        
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")
        return False

if __name__ == "__main__":
    check_admin_user()
