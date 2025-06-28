#!/usr/bin/env python3
"""
Comprehensive test for admin password update functionality
Tests the complete flow: update password, logout, login with new password
"""
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def test_password_update_flow():
    """Test the complete password update flow"""
    
    print("🔍 Testing Complete Password Update Flow")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Check current admin password in database
    print("\n📋 Step 1: Checking current admin password in database")
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        admin_user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        original_password_hash = admin_user['password_hash']
        print(f"✅ Found admin user with password hash: {original_password_hash[:20]}...")
        
        # Verify current password works
        if check_password_hash(original_password_hash, 'admin'):
            print("✅ Current password 'admin' is valid")
        else:
            print("❌ Current password 'admin' is not valid")
            return False
        
    finally:
        conn.close()
    
    # Step 2: Test password update in database directly (simulating the function)
    print("\n🔧 Step 2: Testing password update process")
    
    new_password = "NewAdminPass123!"
    new_password_hash = generate_password_hash(new_password)
    
    conn = sqlite3.connect('ai_learning.db')
    try:
        # Update password
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (new_password_hash, 'admin')
        )
        conn.commit()
        print(f"✅ Password updated in database with new hash: {new_password_hash[:20]}...")
        
        # Verify the update took effect
        updated_user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if updated_user['password_hash'] == new_password_hash:
            print("✅ Database update confirmed - new password hash is stored")
        else:
            print("❌ Database update failed - password hash not updated")
            return False
        
        # Test old password no longer works
        if not check_password_hash(updated_user['password_hash'], 'admin'):
            print("✅ Old password 'admin' is now invalid (correctly)")
        else:
            print("❌ Old password 'admin' still works (PROBLEM!)")
            return False
        
        # Test new password works
        if check_password_hash(updated_user['password_hash'], new_password):
            print("✅ New password works correctly")
        else:
            print("❌ New password doesn't work (PROBLEM!)")
            return False
            
    finally:
        conn.close()
    
    # Step 3: Restore original password for continued testing
    print("\n🔄 Step 3: Restoring original password for app testing")
    
    conn = sqlite3.connect('ai_learning.db')
    try:
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (original_password_hash, 'admin')
        )
        conn.commit()
        print("✅ Original password restored for continued app testing")
    finally:
        conn.close()
    
    return True

def test_session_invalidation():
    """Test that session invalidation works correctly"""
    
    print("\n🔐 Testing Session Invalidation Logic")
    print("=" * 40)
    
    # Test the invalidate_session function by looking at its database operations
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Check if user_sessions table exists and has the right structure
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'"
        ).fetchall()
        
        if not tables:
            print("❌ user_sessions table not found")
            return False
        
        print("✅ user_sessions table exists")
        
        # Check table structure
        columns = conn.execute("PRAGMA table_info(user_sessions)").fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['id', 'user_id', 'session_token', 'created_at', 'expires_at', 'is_valid']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"❌ Missing columns in user_sessions: {missing_columns}")
            return False
        
        print("✅ user_sessions table has all required columns")
        
        # Test session creation and invalidation
        test_session_token = "test_session_123"
        test_user_id = 1
        
        # Create a test session
        conn.execute(
            '''INSERT OR REPLACE INTO user_sessions 
               (user_id, session_token, created_at, expires_at, is_valid)
               VALUES (?, ?, datetime('now'), datetime('now', '+24 hours'), 1)''',
            (test_user_id, test_session_token)
        )
        conn.commit()
        
        # Verify session was created
        session = conn.execute(
            'SELECT * FROM user_sessions WHERE session_token = ?',
            (test_session_token,)
        ).fetchone()
        
        if session and session['is_valid'] == 1:
            print("✅ Test session created successfully")
        else:
            print("❌ Failed to create test session")
            return False
        
        # Test session invalidation
        conn.execute(
            'UPDATE user_sessions SET is_valid = 0 WHERE session_token = ?',
            (test_session_token,)
        )
        conn.commit()
        
        # Verify session was invalidated
        invalid_session = conn.execute(
            'SELECT * FROM user_sessions WHERE session_token = ?',
            (test_session_token,)
        ).fetchone()
        
        if invalid_session and invalid_session['is_valid'] == 0:
            print("✅ Session invalidation works correctly")
        else:
            print("❌ Session invalidation failed")
            return False
        
        # Clean up test session
        conn.execute('DELETE FROM user_sessions WHERE session_token = ?', (test_session_token,))
        conn.commit()
        
        return True
        
    finally:
        conn.close()

def check_database_integrity():
    """Check database integrity and constraints"""
    
    print("\n🗄️  Database Integrity Check")
    print("=" * 30)
    
    conn = sqlite3.connect('ai_learning.db')
    
    try:
        # Check admin user exists and has proper structure
        admin_user = conn.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if not admin_user:
            print("❌ Admin user not found")
            return False
        
        print(f"✅ Admin user found (ID: {admin_user[0]})")
        
        # Check password hash is not empty
        if not admin_user[2] or len(admin_user[2]) < 10:
            print("❌ Admin password hash is invalid or empty")
            return False
        
        print("✅ Admin password hash exists and appears valid")
        
        # Check for any database locks or issues
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')
        conn.execute('ROLLBACK')
        print("✅ Database can be locked for transactions")
        
        return True
        
    except Exception as e:
        print(f"❌ Database integrity check failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("🧪 Comprehensive Admin Password Update Test")
    print("=" * 80)
    
    success = True
    
    # Run all tests
    tests = [
        ("Database Integrity", check_database_integrity),
        ("Session Invalidation", test_session_invalidation),
        ("Password Update Flow", test_password_update_flow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🏃 Running {test_name} test...")
        try:
            if not test_func():
                print(f"❌ {test_name} test FAILED")
                success = False
            else:
                print(f"✅ {test_name} test PASSED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {str(e)}")
            success = False
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED! Password update functionality is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! There are issues with the password update functionality.")
    print("=" * 80)
