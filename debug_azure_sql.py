#!/usr/bin/env python3
"""
Debug Azure SQL and fix admin user issue
"""
import pyodbc
import sys
from werkzeug.security import generate_password_hash

def debug_and_fix_azure_sql():
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:ai-learning-sql-centralus.database.windows.net,1433;Database=ai-learning-db;Uid=ailearningadmin;Pwd=YourSecureAdminPassword123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    
    try:
        print('🔍 Testing Azure SQL connection...')
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print('✅ Connected successfully')
        
        # Check what tables exist
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f'📋 Available tables: {tables}')
        
        # Check if users table exists and has admin user
        if 'users' in tables:
            print('🔍 Checking users table...')
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                print('❌ Admin user not found, creating...')
                password_hash = generate_password_hash('YourSecureAdminPassword123!')
                cursor.execute("""
                    INSERT INTO users (username, password_hash, level, points, created_at) 
                    VALUES (?, ?, ?, ?, GETDATE())
                """, ('admin', password_hash, 'Expert', 1000))
                conn.commit()
                print('✅ Admin user created')
            else:
                print('✅ Admin user exists')
                
            # Get admin user details
            cursor.execute("SELECT id, username, level, points FROM users WHERE username = 'admin'")
            admin_user = cursor.fetchone()
            print(f'👤 Admin user: ID={admin_user[0]}, Username={admin_user[1]}, Level={admin_user[2]}, Points={admin_user[3]}')
        else:
            print('❌ Users table does not exist')
            return False
        
        # Check session table
        session_table = 'user_sessions' if 'user_sessions' in tables else 'sessions'
        if session_table in tables:
            print(f'🔍 Checking {session_table} table...')
            cursor.execute(f"SELECT COUNT(*) FROM {session_table}")
            session_count = cursor.fetchone()[0]
            print(f'📊 Session records: {session_count}')
            
            # Show recent sessions
            cursor.execute(f"SELECT TOP 3 session_token, user_id, created_at, is_active FROM {session_table} ORDER BY created_at DESC")
            sessions = cursor.fetchall()
            for session in sessions:
                print(f'📊 Session: {session[0][:20]}..., User: {session[1]}, Created: {session[2]}, Active: {session[3]}')
        else:
            print('❌ No session table found')
            return False
        
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f'❌ Database error: {e}')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == '__main__':
    success = debug_and_fix_azure_sql()
    sys.exit(0 if success else 1)
