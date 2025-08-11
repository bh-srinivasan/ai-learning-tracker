#!/usr/bin/env python3
"""
Direct Azure SQL Fix - Actually execute the database changes
"""

import os
import sys
import pyodbc
from datetime import datetime

def execute_azure_sql_fix():
    """Actually execute the Azure SQL fixes"""
    
    print("=" * 60)
    print("EXECUTING AZURE SQL DATABASE FIX")
    print("=" * 60)
    
    # Try to get Azure SQL connection details from environment
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USERNAME') 
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    # If not in environment, try common Azure patterns
    if not all([server, database, username, password]):
        print("🔍 Azure SQL environment variables not found locally")
        print("Attempting to connect using common Azure patterns...")
        
        # Try to extract from connection string if available
        conn_str = os.environ.get('DATABASE_URL') or os.environ.get('SQLAZURECONNSTR_defaultConnection')
        if conn_str:
            print(f"Found connection string: {conn_str[:50]}...")
        else:
            print("❌ No Azure SQL connection information available")
            print("Please set Azure SQL environment variables:")
            print("- AZURE_SQL_SERVER")
            print("- AZURE_SQL_DATABASE") 
            print("- AZURE_SQL_USERNAME")
            print("- AZURE_SQL_PASSWORD")
            return False
    
    try:
        # Build connection string
        if all([server, database, username, password]):
            # Direct connection
            if not server.endswith('.database.windows.net'):
                server = f"{server}.database.windows.net"
            
            conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        
        print(f"🔗 Connecting to Azure SQL: {database} on {server}")
        
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        print("✅ Connected to Azure SQL Database")
        
        # Execute the fixes
        print("\n1. Adding is_admin column...")
        try:
            # Check if column exists
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
            """)
            
            if cursor.fetchone()[0] == 0:
                print("   Adding is_admin column...")
                cursor.execute("ALTER TABLE users ADD is_admin BIT DEFAULT 0")
                conn.commit()
                print("   ✅ is_admin column added")
            else:
                print("   ✅ is_admin column already exists")
                
        except Exception as e:
            print(f"   ❌ Error with column: {e}")
            return False
        
        # Set admin privileges
        print("\n2. Setting admin privileges...")
        try:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('admin',))
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected > 0:
                print(f"   ✅ Admin privileges set (rows affected: {rows_affected})")
            else:
                print("   ⚠️  No rows updated - checking if admin user exists...")
                
                cursor.execute("SELECT id, username FROM users WHERE username = ?", ('admin',))
                admin_user = cursor.fetchone()
                if admin_user:
                    print(f"   ✅ Admin user exists (ID: {admin_user[0]})")
                else:
                    print("   ❌ Admin user not found in database!")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error setting privileges: {e}")
            return False
        
        # Verify the fix
        print("\n3. Verifying fix...")
        try:
            cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", ('admin',))
            admin_user = cursor.fetchone()
            
            if admin_user and len(admin_user) >= 3:
                print(f"   ✅ Verification successful:")
                print(f"      User ID: {admin_user[0]}")
                print(f"      Username: {admin_user[1]}")
                print(f"      Is Admin: {admin_user[2]}")
                
                if admin_user[2]:
                    print("   ✅ Admin privileges confirmed!")
                    return True
                else:
                    print("   ❌ Admin privileges not set correctly")
                    return False
            else:
                print("   ❌ Could not verify admin user")
                return False
                
        except Exception as e:
            print(f"   ❌ Verification error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nPossible solutions:")
        print("1. Check Azure SQL server firewall rules")
        print("2. Verify connection credentials")
        print("3. Install ODBC Driver 17 for SQL Server")
        return False
    finally:
        try:
            conn.close()
            print("\n🔗 Database connection closed")
        except:
            pass
    
    print("=" * 60)

if __name__ == "__main__":
    print("Azure SQL Database Fix Execution")
    print("This will actually modify the Azure database")
    print()
    
    success = execute_azure_sql_fix()
    
    if success:
        print("🎉 Azure SQL fix completed successfully!")
        print("Now deploy the code changes and test...")
    else:
        print("❌ Azure SQL fix failed!")
        print("Manual database fix may be required.")
