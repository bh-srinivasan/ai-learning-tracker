import pyodbc
import traceback
import secrets
from datetime import datetime, timedelta

# Test Azure SQL connection and session creation
import os
server = 'ai-learning-sql-centralus.database.windows.net'
database = 'ai-learning-db'
username = 'ailearningadmin'
password = os.environ.get('AZURE_SQL_PASSWORD', 'AiAzurepass!2025')

# Connection string
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("=================================")
print("Azure SQL Session Creation Test")
print("=================================")

try:
    # Connect to the database
    print("🔗 Connecting to Azure SQL Database...")
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ Connected successfully!")
    
    # Test session creation like the app does
    print("\n🔍 Testing session creation process...")
    
    # 1. Check if user_sessions table exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'user_sessions'
    """)
    table_exists = cursor.fetchone()[0]
    print(f"✅ user_sessions table exists: {table_exists > 0}")
    
    if table_exists == 0:
        print("❌ user_sessions table does not exist!")
        # Check if sessions table exists instead
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'sessions'
        """)
        sessions_table_exists = cursor.fetchone()[0]
        print(f"✅ sessions table exists: {sessions_table_exists > 0}")
    
    # 2. Get admin user ID
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    if admin_user:
        user_id = admin_user[0]
        print(f"✅ Admin user found with ID: {user_id}")
    else:
        print("❌ Admin user not found!")
        cursor.close()
        conn.close()
        exit(1)
    
    # 3. Test session creation
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)
    session_table = 'user_sessions' if table_exists > 0 else 'sessions'
    
    print(f"\n🔧 Creating test session...")
    print(f"   Table: {session_table}")
    print(f"   Token: {session_token[:10]}...")
    print(f"   User ID: {user_id}")
    
    # Invalidate old sessions for this user
    cursor.execute(f'''
        UPDATE {session_table} 
        SET is_active = 0 
        WHERE user_id = ? AND is_active = 1
    ''', (user_id,))
    print(f"✅ Invalidated old sessions")
    
    # Create new session
    cursor.execute(f'''
        INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_token, user_id, '127.0.0.1', 'Test-Agent', expires_at))
    
    conn.commit()
    print("✅ Session created successfully!")
    
    # 4. Verify session was created
    cursor.execute(f'''
        SELECT session_token, user_id, ip_address, expires_at 
        FROM {session_table} 
        WHERE session_token = ?
    ''', (session_token,))
    
    created_session = cursor.fetchone()
    if created_session:
        print(f"✅ Session verified in database:")
        print(f"   Token: {created_session[0][:10]}...")
        print(f"   User ID: {created_session[1]}")
        print(f"   IP: {created_session[2]}")
        print(f"   Expires: {created_session[3]}")
    else:
        print("❌ Session not found after creation!")
    
    cursor.close()
    conn.close()
    print("\n🎉 Azure SQL session creation test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
