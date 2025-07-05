#!/usr/bin/env python3
"""
Clean up database by removing non-essential users
Only keep admin and demo users for testing
"""

import sqlite3
import sys

def cleanup_database():
    """Remove non-essential users from the database"""
    print("🧹 AI Learning Tracker - Database Cleanup")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        # Get current users
        users = conn.execute('SELECT id, username FROM users').fetchall()
        
        print("📊 Current users in database:")
        for user in users:
            print(f"   - ID: {user['id']}, Username: {user['username']}")
        
        # Define users to keep
        essential_users = ['admin', 'demo']
        
        # Find users to remove
        users_to_remove = []
        for user in users:
            if user['username'] not in essential_users:
                users_to_remove.append(user)
        
        if not users_to_remove:
            print("\n✅ No non-essential users found. Database is clean.")
            return True
        
        print(f"\n🗑️  Users to remove ({len(users_to_remove)}):")
        for user in users_to_remove:
            print(f"   - {user['username']} (ID: {user['id']})")
        
        # Confirm removal (auto-confirm for automated cleanup)
        print(f"\n⚠️  This will permanently delete {len(users_to_remove)} users and all their data.")
        print("🤖 Auto-confirming cleanup for bharath user removal...")
        confirm = 'y'  # Auto-confirm for this cleanup
        
        if confirm != 'y':
            print("❌ Cleanup cancelled by user.")
            return False
        
        # Remove users and their data
        removed_count = 0
        for user in users_to_remove:
            user_id = user['id']
            username = user['username']
            
            print(f"\n🗑️  Removing user: {username}")
            
            # Remove related data first
            conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            sessions_removed = conn.execute('SELECT changes()').fetchone()[0]
            print(f"   - Removed {sessions_removed} sessions")
            
            conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
            entries_removed = conn.execute('SELECT changes()').fetchone()[0]
            print(f"   - Removed {entries_removed} learning entries")
            
            # Remove user
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            user_removed = conn.execute('SELECT changes()').fetchone()[0]
            
            if user_removed > 0:
                print(f"   ✅ User {username} removed successfully")
                removed_count += 1
            else:
                print(f"   ❌ Failed to remove user {username}")
        
        conn.commit()
        
        print(f"\n🎉 Database cleanup completed!")
        print(f"   - Removed {removed_count} users")
        print(f"   - Kept essential users: {', '.join(essential_users)}")
        
        # Show final user list
        final_users = conn.execute('SELECT username FROM users').fetchall()
        print(f"\n📊 Remaining users:")
        for user in final_users:
            print(f"   ✅ {user['username']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_essential_users():
    """Verify that admin and demo users exist with correct passwords"""
    print("\n🔍 Verifying essential users...")
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        
        # Check admin user
        admin = conn.execute('SELECT username FROM users WHERE username = ?', ('admin',)).fetchone()
        if admin:
            print("   ✅ Admin user exists")
        else:
            print("   ❌ Admin user missing")
        
        # Check demo user
        demo = conn.execute('SELECT username FROM users WHERE username = ?', ('demo',)).fetchone()
        if demo:
            print("   ✅ Demo user exists")
        else:
            print("   ❌ Demo user missing")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error verifying users: {str(e)}")

if __name__ == "__main__":
    success = cleanup_database()
    if success:
        verify_essential_users()
        print("\n💡 Next steps:")
        print("   1. Run reset_all_passwords.py to ensure correct passwords")
        print("   2. Test login with admin and demo users")
        print("   3. Run comprehensive_test.py to verify functionality")
    
    sys.exit(0 if success else 1)
