#!/usr/bin/env python3
"""
Azure SQL Database Admin Column Fix
Adds the is_admin column and sets admin user properly
"""

import os
import pyodbc
from datetime import datetime

def fix_azure_admin_column():
    """Fix the Azure SQL database to add is_admin column and set admin user"""
    
    print("=" * 60)
    print("AZURE SQL DATABASE ADMIN COLUMN FIX")
    print("=" * 60)
    
    # Azure SQL connection parameters
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE') 
    username = os.environ.get('AZURE_SQL_USERNAME')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    if not all([server, database, username, password]):
        print("❌ Missing Azure SQL environment variables")
        print("Required: AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD")
        return False
    
    try:
        # Connection string for Azure SQL
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        
        print(f"🔗 Connecting to Azure SQL Database: {database}")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1: Check if is_admin column exists
        print("\n1. Checking if is_admin column exists...")
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
            """)
            column_exists = cursor.fetchone()[0] > 0
            
            if column_exists:
                print("   ✅ is_admin column already exists")
            else:
                print("   ❌ is_admin column missing - adding it...")
                cursor.execute("ALTER TABLE users ADD is_admin BIT DEFAULT 0")
                conn.commit()
                print("   ✅ is_admin column added successfully")
        
        except Exception as e:
            print(f"   ❌ Error checking/adding column: {e}")
            return False
        
        # Step 2: Check admin user and set is_admin = 1
        print("\n2. Setting admin user privileges...")
        try:
            # Check if admin user exists
            cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", ('admin',))
            admin_user = cursor.fetchone()
            
            if admin_user:
                print(f"   ✅ Admin user found: ID={admin_user[0]}, is_admin={admin_user[2]}")
                
                if not admin_user[2]:  # is_admin is 0 or None
                    print("   🔧 Setting admin privileges...")
                    cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('admin',))
                    conn.commit()
                    print("   ✅ Admin privileges set successfully")
                else:
                    print("   ✅ Admin privileges already set")
            else:
                print("   ❌ Admin user not found in database")
                return False
                
        except Exception as e:
            print(f"   ❌ Error setting admin privileges: {e}")
            return False
        
        # Step 3: Verify the fix
        print("\n3. Verifying the fix...")
        try:
            cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", ('admin',))
            admin_user = cursor.fetchone()
            
            if admin_user and admin_user[2]:
                print(f"   ✅ Verification successful: Admin user (ID={admin_user[0]}) has is_admin=1")
                return True
            else:
                print("   ❌ Verification failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verifying fix: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    finally:
        try:
            conn.close()
            print("\n🔗 Database connection closed")
        except:
            pass
    
    print("=" * 60)

if __name__ == "__main__":
    success = fix_azure_admin_column()
    if success:
        print("🎉 Azure SQL database fix completed successfully!")
    else:
        print("❌ Azure SQL database fix failed!")
