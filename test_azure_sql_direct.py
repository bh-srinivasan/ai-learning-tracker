#!/usr/bin/env python3
"""
Direct Azure SQL Database Connection Test
Test Azure SQL Database connection with available drivers
"""

import os
import pyodbc

def test_azure_sql_direct():
    """Test direct connection to Azure SQL Database"""
    print("🔍 DIRECT AZURE SQL DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # Get Azure SQL credentials
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USERNAME')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    print(f"🔗 Connecting to Azure SQL:")
    print(f"   Server: {server}")
    print(f"   Database: {database}")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password) if password else 'Not set'}")
    
    # Try different ODBC drivers
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server", 
        "SQL Server"
    ]
    
    for driver in drivers_to_try:
        print(f"\n🔧 Trying driver: {driver}")
        
        connection_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        try:
            print(f"   📡 Attempting connection...")
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            print(f"   ✅ SUCCESS! Connected to Azure SQL with {driver}")
            
            # Test basic query
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            print(f"   📊 SQL Server Version: {version[:50]}...")
            
            # Check if tables exist
            cursor.execute("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            print(f"   📋 Tables found: {table_count}")
            
            if table_count > 0:
                # Check for users table
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = 'users'
                """)
                users_table_exists = cursor.fetchone()[0] > 0
                
                if users_table_exists:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    print(f"   👥 Users in Azure SQL: {user_count}")
                    
                    # Check admin user
                    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
                    admin_exists = cursor.fetchone()[0] > 0
                    print(f"   🔐 Admin user exists: {'Yes' if admin_exists else 'No'}")
                else:
                    print(f"   ⚠️  Users table not found")
            
            conn.close()
            
            print(f"\n✅ AZURE SQL DATABASE VERIFICATION SUCCESSFUL")
            print(f"✅ Working driver: {driver}")
            return True
            
        except pyodbc.Error as e:
            print(f"   ❌ Failed with {driver}: {e}")
            continue
        except Exception as e:
            print(f"   ❌ Unexpected error with {driver}: {e}")
            continue
    
    print(f"\n❌ ALL DRIVERS FAILED")
    print(f"❌ Could not connect to Azure SQL Database")
    
    # Additional troubleshooting
    print(f"\n🔍 Troubleshooting Information:")
    print(f"   Available drivers: {pyodbc.drivers()}")
    
    # Test if server is reachable
    import socket
    try:
        host, port = server.split(',') if ',' in server else (server, 1433)
        port = int(port) if isinstance(port, str) else port
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Server {host}:{port} is reachable")
        else:
            print(f"   ❌ Server {host}:{port} is not reachable")
    except Exception as e:
        print(f"   ❓ Could not test server connectivity: {e}")
    
    return False

if __name__ == "__main__":
    test_azure_sql_direct()
