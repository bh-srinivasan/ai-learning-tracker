#!/usr/bin/env python3
"""
Azure Database ONLY Verification Tool
Connects specifically to Azure SQL Database, NOT local SQLite
"""

import os
import logging
from database_manager import DatabaseManager

def check_azure_database_only():
    """Check ONLY Azure database - force Azure SQL connection"""
    print("🔍 AZURE SQL DATABASE VERIFICATION")
    print("=" * 60)
    print("⚠️  AZURE SQL DATABASE ONLY - NO LOCAL CHECKING")
    print("=" * 60)
    
    # Force production environment to use Azure SQL
    original_env = os.environ.get('ENV')
    os.environ['ENV'] = 'production'
    
    try:
        # Create new database manager with production environment
        db_manager = DatabaseManager()
        
        if not db_manager.is_azure_sql:
            print("❌ FAILED TO CONNECT TO AZURE SQL DATABASE!")
            print("❌ Database manager is using SQLite instead of Azure SQL")
            
            # Check what's missing
            required_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
            missing_vars = []
            
            for var in required_vars:
                if not os.environ.get(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"❌ Missing environment variables: {missing_vars}")
            else:
                print("✅ All Azure SQL environment variables are present")
                print("❌ But connection to Azure SQL still failed")
            
            return False
        
        print("✅ SUCCESSFULLY CONNECTED TO AZURE SQL DATABASE")
        print(f"🔗 Connection type: {db_manager.connection_string}")
        
        # Get Azure SQL connection
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check tables in Azure SQL
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📊 AZURE SQL DATABASE: Found {len(tables)} tables")
        
        # Check each table
        for table_row in tables:
            table_name = table_row[0]
            print(f"\n🔍 AZURE TABLE: {table_name}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            count = cursor.fetchone()[0]
            
            print(f"   📈 Row count: {count}")
            
            # Get column info
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? 
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            columns = cursor.fetchall()
            print(f"   📋 Columns ({len(columns)}):")
            
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"      - {col[0]} ({col[1]}) {nullable}{default}")
        
        # Check critical data in Azure SQL
        print(f"\n=== AZURE SQL CRITICAL DATA CHECK ===")
        
        # Check admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print("✅ Admin user exists in Azure SQL")
            
            cursor.execute("""
                SELECT username, level, points, status, last_login, login_count 
                FROM users WHERE username = 'admin'
            """)
            admin = cursor.fetchone()
            print(f"   - Level: {admin[1] or 'Not set'}")
            print(f"   - Points: {admin[2] or 0}")
            print(f"   - Status: {admin[3] or 'active'}")
            print(f"   - Last Login: {admin[4] or 'Never'}")
            print(f"   - Login Count: {admin[5] or 0}")
        else:
            print("❌ Admin user MISSING in Azure SQL!")
        
        # Check total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"👥 Total users in Azure SQL: {total_users}")
        
        # Check courses
        cursor.execute("SELECT COUNT(*) FROM courses")
        total_courses = cursor.fetchone()[0]
        print(f"📚 Total courses in Azure SQL: {total_courses}")
        
        # Check recent activity
        cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1")
        active_sessions = cursor.fetchone()[0]
        print(f"🔐 Active sessions in Azure SQL: {active_sessions}")
        
        conn.close()
        
        print(f"\n✅ AZURE SQL DATABASE VERIFICATION COMPLETE")
        print(f"✅ Database is properly initialized and operational")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Azure SQL Database: {e}")
        
        # Additional debugging
        print(f"\n🔍 Debug Information:")
        print(f"   ENV setting: {os.environ.get('ENV')}")
        print(f"   AZURE_SQL_SERVER: {os.environ.get('AZURE_SQL_SERVER', 'Not set')}")
        print(f"   AZURE_SQL_DATABASE: {os.environ.get('AZURE_SQL_DATABASE', 'Not set')}")
        print(f"   AZURE_SQL_USERNAME: {os.environ.get('AZURE_SQL_USERNAME', 'Not set')}")
        print(f"   AZURE_SQL_PASSWORD: {'Set' if os.environ.get('AZURE_SQL_PASSWORD') else 'Not set'}")
        
        return False
        
    finally:
        # Restore original environment
        if original_env:
            os.environ['ENV'] = original_env
        elif 'ENV' in os.environ:
            del os.environ['ENV']

if __name__ == "__main__":
    # Suppress INFO logs for cleaner output
    logging.getLogger().setLevel(logging.WARNING)
    
    success = check_azure_database_only()
    
    if not success:
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Verify Azure SQL Database is running")
        print("   2. Check network connectivity to Azure")
        print("   3. Verify credentials are correct")
        print("   4. Check if firewall allows connection")
