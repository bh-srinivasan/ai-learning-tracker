#!/usr/bin/env python3
"""
Debug script to analyze non-admin login authentication flow
This script will test the login process locally to identify the issue
"""

import os
import sys
import sqlite3
import hashlib
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app functions
try:
    from app import get_db_connection, is_azure_sql, get_session_table, create_user_session
    print("✅ Successfully imported app functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def debug_non_admin_login():
    print("=== NON-ADMIN LOGIN DEBUG ANALYSIS ===\n")
    
    # 1. Check database connection
    print("1. Testing database connection...")
    try:
        conn = get_db_connection()
        print("✅ Database connection successful")
        
        # Check if we're using Azure SQL or local SQLite
        azure_mode = is_azure_sql()
        session_table = get_session_table()
        print(f"✅ Environment: {'Azure SQL' if azure_mode else 'Local SQLite'}")
        print(f"✅ Session table: {session_table}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # 2. Check users table and find non-admin users
    print("\n2. Analyzing users table...")
    try:
        conn = get_db_connection()
        
        # Get all users
        users = conn.execute("SELECT id, username, is_admin FROM users ORDER BY id").fetchall()
        print(f"✅ Found {len(users)} users in database:")
        
        admin_users = []
        non_admin_users = []
        
        for user in users:
            is_admin = bool(user['is_admin']) if user['is_admin'] is not None else False
            user_type = "ADMIN" if is_admin else "NON-ADMIN"
            print(f"   - ID: {user['id']}, Username: {user['username']}, Type: {user_type}")
            
            if is_admin:
                admin_users.append(user)
            else:
                non_admin_users.append(user)
        
        print(f"✅ Admin users: {len(admin_users)}")
        print(f"✅ Non-admin users: {len(non_admin_users)}")
        
        conn.close()
        
        # Test with a non-admin user if available
        if non_admin_users:
            test_user = non_admin_users[0]
            print(f"\n3. Testing session creation for non-admin user: {test_user['username']}")
            test_session_creation(test_user['id'])
        else:
            print("\n⚠️  No non-admin users found to test with")
            
    except Exception as e:
        print(f"❌ Error analyzing users: {e}")
        import traceback
        traceback.print_exc()

def test_session_creation(user_id):
    """Test session creation for a specific user"""
    try:
        print(f"   Testing session creation for user ID: {user_id}")
        
        # Create a test session
        session_token = create_user_session(user_id, "127.0.0.1", "Test-Agent")
        
        if session_token:
            print(f"✅ Session created successfully: {session_token[:16]}...")
            
            # Verify session exists in database
            conn = get_db_connection()
            session_table = get_session_table()
            
            session_check = conn.execute(f'''
                SELECT s.*, u.username, u.is_admin 
                FROM {session_table} s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.session_token = ?
            ''', (session_token,)).fetchone()
            
            if session_check:
                print(f"✅ Session verified in database")
                print(f"   - User: {session_check['username']}")
                print(f"   - Is Admin: {session_check['is_admin']}")
                print(f"   - Session Active: {session_check['is_active']}")
            else:
                print(f"❌ Session not found in database")
            
            conn.close()
            
        else:
            print(f"❌ Session creation failed")
            
    except Exception as e:
        print(f"❌ Error testing session creation: {e}")
        import traceback
        traceback.print_exc()

def check_login_route_compatibility():
    """Check if login route logic is compatible with current database schema"""
    print("\n4. Checking login route compatibility...")
    
    try:
        conn = get_db_connection()
        session_table = get_session_table()
        
        # Test the exact query used in get_current_user
        print(f"   Testing get_current_user query structure...")
        test_query = f'''
            SELECT s.*, u.username, u.level, u.points, u.is_admin 
            FROM {session_table} s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = ?
        '''
        
        # Execute with dummy values to test structure
        try:
            result = conn.execute(test_query, ("dummy_token", True)).fetchone()
            print(f"✅ Query structure is valid (no results expected)")
        except Exception as e:
            print(f"❌ Query structure error: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking compatibility: {e}")

if __name__ == "__main__":
    debug_non_admin_login()
    check_login_route_compatibility()
    print("\n=== DEBUG ANALYSIS COMPLETE ===")
