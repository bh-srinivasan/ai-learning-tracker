#!/usr/bin/env python3
"""
Reset admin password to 'admin' for consistency
"""
import sqlite3
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset admin password to 'admin'"""
    
    print("🔄 RESETTING ADMIN PASSWORD TO DEFAULT")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    
    try:
        # Generate new password hash for 'admin'
        new_password = 'admin'
        new_password_hash = generate_password_hash(new_password)
        
        print(f"🔑 New password: '{new_password}'")
        print(f"🔒 New hash: {new_password_hash[:30]}...")
        
        # Update admin password
        cursor = conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (new_password_hash, 'admin')
        )
        
        if cursor.rowcount == 1:
            conn.commit()
            print("✅ Admin password successfully reset to 'admin'")
            
            # Verify the change
            admin_user = conn.execute(
                'SELECT username, password_hash FROM users WHERE username = ?',
                ('admin',)
            ).fetchone()
            
            print(f"✅ Verification: Admin user found with new hash")
            return True
            
        else:
            print("❌ Failed to update admin password")
            return False
            
    except Exception as e:
        print(f"❌ Error resetting password: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = reset_admin_password()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("   Admin password has been reset to: 'admin'")
        print("   You can now login with: admin/admin")
        print("   All test scripts will work with this password.")
    else:
        print("\n❌ FAILED!")
        print("   Could not reset admin password.")
