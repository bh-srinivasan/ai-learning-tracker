#!/usr/bin/env python3
"""
Direct test of admin password change database operations
"""
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def test_direct_password_change():
    """Test password change directly with database operations"""
    
    print("🔍 Direct Password Change Test")
    print("=" * 40)
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row  # This enables dict-like access
    
    try:
        # Step 1: Get current admin user
        print("Step 1: Fetching admin user...")
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', 
            ('admin',)
        ).fetchone()
        
        if not user:
            print("❌ Admin user not found")
            return False
        
        print(f"✅ Admin user found: ID={user['id']}, Username={user['username']}")
        print(f"✅ Current password hash: {user['password_hash'][:30]}...")
        
        # Step 2: Verify current password
        current_password = 'admin'
        if check_password_hash(user['password_hash'], current_password):
            print("✅ Current password verification successful")
        else:
            print("❌ Current password verification failed")
            return False
        
        # Step 3: Generate new password hash
        new_password = 'NewAdminPass123!'
        new_password_hash = generate_password_hash(new_password)
        print(f"✅ New password hash generated: {new_password_hash[:30]}...")
        
        # Step 4: Update password in database
        print("Step 4: Updating password in database...")
        result = conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (new_password_hash, 'admin')
        )
        conn.commit()
        
        if result.rowcount == 1:
            print("✅ Password update successful (1 row affected)")
        else:
            print(f"❌ Password update failed ({result.rowcount} rows affected)")
            return False
        
        # Step 5: Verify update took effect
        print("Step 5: Verifying password update...")
        updated_user = conn.execute(
            'SELECT * FROM users WHERE username = ?', 
            ('admin',)
        ).fetchone()
        
        if updated_user['password_hash'] == new_password_hash:
            print("✅ Password hash correctly updated in database")
        else:
            print("❌ Password hash not updated correctly")
            return False
        
        # Step 6: Test old password no longer works
        if not check_password_hash(updated_user['password_hash'], current_password):
            print("✅ Old password correctly invalidated")
        else:
            print("❌ Old password still works (CRITICAL ISSUE)")
            return False
        
        # Step 7: Test new password works
        if check_password_hash(updated_user['password_hash'], new_password):
            print("✅ New password works correctly")
        else:
            print("❌ New password doesn't work")
            return False
        
        # Step 8: Restore original password
        print("Step 8: Restoring original password...")
        original_hash = user['password_hash']  # From step 1
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (original_hash, 'admin')
        )
        conn.commit()
        print("✅ Original password restored")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def test_session_management():
    """Test session creation and invalidation"""
    
    print("\n🔐 Session Management Test")
    print("=" * 30)
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Create a test session
        test_token = "test_session_12345"
        test_user_id = 1
        
        print("Creating test session...")
        conn.execute('''
            INSERT OR REPLACE INTO user_sessions 
            (user_id, session_token, created_at, expires_at, ip_address, user_agent, is_active)
            VALUES (?, ?, datetime('now'), datetime('now', '+24 hours'), '127.0.0.1', 'Test', 1)
        ''', (test_user_id, test_token))
        conn.commit()
        
        # Verify session was created
        session = conn.execute(
            'SELECT * FROM user_sessions WHERE session_token = ?',
            (test_token,)
        ).fetchone()
        
        if session and session['is_active'] == 1:
            print("✅ Test session created successfully")
        else:
            print("❌ Failed to create test session")
            return False
        
        # Test session invalidation
        print("Invalidating test session...")
        conn.execute(
            'UPDATE user_sessions SET is_active = 0 WHERE session_token = ?',
            (test_token,)
        )
        conn.commit()
        
        # Verify session was invalidated
        invalid_session = conn.execute(
            'SELECT * FROM user_sessions WHERE session_token = ?',
            (test_token,)
        ).fetchone()
        
        if invalid_session and invalid_session['is_active'] == 0:
            print("✅ Session invalidated successfully")
        else:
            print("❌ Session invalidation failed")
            return False
        
        # Clean up
        conn.execute('DELETE FROM user_sessions WHERE session_token = ?', (test_token,))
        conn.commit()
        print("✅ Test session cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during session test: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("🧪 Direct Database Operations Test")
    print("=" * 50)
    
    success = True
    
    # Test password change
    if not test_direct_password_change():
        success = False
    
    # Test session management
    if not test_session_management():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("   ✅ Password changes work correctly")
        print("   ✅ Old passwords are properly invalidated")
        print("   ✅ New passwords work immediately")
        print("   ✅ Session management works correctly")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the output above for specific issues")
    print("=" * 50)
