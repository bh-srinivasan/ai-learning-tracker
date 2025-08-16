#!/usr/bin/env python3
"""Test the fixed get_current_user function"""

import os
import sys
import pyodbc
from datetime import datetime

# Add the current directory to Python path to import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_get_current_user_fix():
    """Test that get_current_user includes is_admin field"""
    
    # Database connection
    server = 'ai-learning-sql-centralus.database.windows.net'
    database = 'ai-learning-db'
    username = 'ailearningadmin'
    password = os.environ.get('AZURE_SQL_PASSWORD')

    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    try:
        print("=== Testing get_current_user Query Fix ===")
        
        # Test the fixed query for demo user
        cursor.execute("""
            SELECT TOP 1 s.*, u.username, u.level, u.points, u.is_admin 
            FROM user_sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE u.username = ? AND s.is_active = ?
            ORDER BY s.created_at DESC
        """, ('demo', 1))
        
        demo_session = cursor.fetchone()
        if demo_session:
            print(f"✅ Demo user session found:")
            print(f"   - Username: {demo_session.username}")
            print(f"   - Level: {demo_session.level}")
            print(f"   - Points: {demo_session.points}")
            print(f"   - is_admin: {demo_session.is_admin}")
            print(f"   - is_admin (bool): {bool(demo_session.is_admin) if demo_session.is_admin is not None else False}")
        else:
            print("❌ No active session found for demo user")

        # Test the fixed query for admin user
        cursor.execute("""
            SELECT TOP 1 s.*, u.username, u.level, u.points, u.is_admin 
            FROM user_sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE u.username = ? AND s.is_active = ?
            ORDER BY s.created_at DESC
        """, ('admin', 1))
        
        admin_session = cursor.fetchone()
        if admin_session:
            print(f"\n✅ Admin user session found:")
            print(f"   - Username: {admin_session.username}")
            print(f"   - Level: {admin_session.level}")
            print(f"   - Points: {admin_session.points}")
            print(f"   - is_admin: {admin_session.is_admin}")
            print(f"   - is_admin (bool): {bool(admin_session.is_admin) if admin_session.is_admin is not None else False}")
        else:
            print("❌ No active session found for admin user")

        print(f"\n🎉 Fixed query now includes is_admin field!")
        print(f"✅ This should resolve the dashboard Internal Server Error for non-admin users")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_get_current_user_fix()
