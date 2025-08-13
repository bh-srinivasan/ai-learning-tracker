#!/usr/bin/env python3
"""
Fix Non-Admin Login Issue
Adds the missing is_admin column to Azure SQL users table if needed
"""
import os
import pyodbc
import sys

def fix_non_admin_login():
    server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
    database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
    username = os.environ.get('AZURE_SQL_USERNAME', 'ailearningadmin')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    if not password:
        print("❌ Error: AZURE_SQL_PASSWORD environment variable not set")
        return False
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    try:
        print("🔄 Connecting to Azure SQL Database...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        # Check if is_admin column exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin' """)
        column_exists = cursor.fetchone()[0] > 0
        if column_exists:
            print("✅ is_admin column already exists")
        else:
            print("🔄 Adding is_admin column to users table...")
            cursor.execute("ALTER TABLE users ADD is_admin BIT NOT NULL DEFAULT 0")
            conn.commit()
            print("✅ is_admin column added successfully!")
        # Update admin user
        print("🔄 Setting admin user as admin...")
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
        conn.commit()
        print("✅ Admin user updated")
        cursor.close()
        conn.close()
        print("\n🎉 SUCCESS: Non-admin login issue fixed!")
        return True
    except pyodbc.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== Non-Admin Login Fix ===")
    success = fix_non_admin_login()
    sys.exit(0 if success else 1)
