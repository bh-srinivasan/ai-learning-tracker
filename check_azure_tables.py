#!/usr/bin/env python3
"""
Debug script to check Azure SQL tables and session structure
"""
import pyodbc
import os

def check_azure_sql_tables():
    try:
        # Get connection string from environment
        connection_string = os.environ.get('AZURE_SQL_CONNECTION_STRING')
        if not connection_string:
            print("❌ No AZURE_SQL_CONNECTION_STRING found")
            return
            
        print(f"🔗 Connecting with: {connection_string[:50]}...")
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Check what tables exist
        print("\n📋 Tables in Azure SQL Database:")
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check users table
        print("\n👤 Users in database:")
        cursor.execute("SELECT id, username, is_admin FROM users ORDER BY id")
        users = cursor.fetchall()
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Admin: {user[2]}")
        
        # Check sessions table (both possible names)
        print("\n🔑 Checking sessions...")
        
        # Try user_sessions first
        try:
            cursor.execute("SELECT TOP 5 * FROM user_sessions ORDER BY created_at DESC")
            sessions = cursor.fetchall()
            print(f"  - user_sessions table: {len(sessions)} recent sessions")
            for session in sessions:
                print(f"    Session ID: {session[0]}, User ID: {session[1]}, Created: {session[2]}")
        except Exception as e:
            print(f"  - user_sessions table error: {e}")
        
        # Try sessions table
        try:
            cursor.execute("SELECT TOP 5 * FROM sessions ORDER BY created_at DESC")
            sessions = cursor.fetchall()
            print(f"  - sessions table: {len(sessions)} recent sessions")
            for session in sessions:
                print(f"    Session ID: {session[0]}, User ID: {session[1]}, Created: {session[2]}")
        except Exception as e:
            print(f"  - sessions table error: {e}")
        
        conn.close()
        print("\n✅ Azure SQL check complete")
        
    except Exception as e:
        print(f"❌ Error connecting to Azure SQL: {e}")

if __name__ == "__main__":
    check_azure_sql_tables()
