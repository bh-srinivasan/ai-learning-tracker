#!/usr/bin/env python3
"""
Azure SQL Database Structure Verification
ONLY checks the REAL Azure SQL Database
"""

import os
import pyodbc

def check_real_azure_database():
    """Check the REAL Azure SQL Database structure and data"""
    print("🔍 REAL AZURE SQL DATABASE VERIFICATION")
    print("=" * 60)
    print("⚠️  AZURE SQL DATABASE ONLY - NO LOCAL SQLITE")
    print("=" * 60)
    
    # Azure SQL connection details
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USERNAME')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    # Use working driver
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print(f"✅ Connected to Azure SQL Database: {database}")
        print(f"🔗 Server: {server}")
        
        # Get all tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 AZURE SQL DATABASE: Found {len(tables)} tables")
        
        # Analyze each table
        for table_name in tables:
            print(f"\n🔍 AZURE TABLE: {table_name}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            count = cursor.fetchone()[0]
            
            # Get column information
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME, 
                    DATA_TYPE, 
                    IS_NULLABLE, 
                    COLUMN_DEFAULT,
                    CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? 
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            print(f"   📈 Row count: {count}")
            print(f"   📋 Columns ({len(columns)}):")
            
            for col in columns:
                col_name, data_type, nullable, default, max_length = col
                
                # Format data type
                if max_length and data_type in ['varchar', 'nvarchar', 'char', 'nchar']:
                    data_type = f"{data_type}({max_length})"
                
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                
                print(f"      - {col_name:<20} {data_type:<15} {nullable_str}{default_str}")
            
            # Show sample data for important tables
            if table_name in ['users', 'courses', 'level_settings'] and count > 0:
                print(f"   📝 Sample Data:")
                
                if table_name == 'users':
                    cursor.execute("""
                        SELECT TOP 5 id, username, level, points, status, login_count, last_login
                        FROM users 
                        ORDER BY id
                    """)
                elif table_name == 'courses':
                    cursor.execute("""
                        SELECT TOP 3 id, title, source, level, points
                        FROM courses 
                        ORDER BY id
                    """)
                elif table_name == 'level_settings':
                    cursor.execute("""
                        SELECT level_name, points_required 
                        FROM level_settings 
                        ORDER BY points_required
                    """)
                
                sample_data = cursor.fetchall()
                for row in sample_data:
                    print(f"      {row}")
        
        # Critical data verification
        print(f"\n=== AZURE SQL CRITICAL DATA VERIFICATION ===")
        
        # Check admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print("✅ Admin user exists in Azure SQL")
            
            cursor.execute("""
                SELECT username, level, points, status, last_login, login_count, created_at
                FROM users WHERE username = 'admin'
            """)
            admin = cursor.fetchone()
            print(f"   👤 Username: {admin[0]}")
            print(f"   🎯 Level: {admin[1] or 'Not set'}")
            print(f"   🏆 Points: {admin[2] or 0}")
            print(f"   📊 Status: {admin[3] or 'active'}")
            print(f"   🔐 Last Login: {admin[4] or 'Never'}")
            print(f"   📈 Login Count: {admin[5] or 0}")
            print(f"   📅 Created: {admin[6] or 'Unknown'}")
        else:
            print("❌ CRITICAL: Admin user MISSING in Azure SQL!")
        
        # Check total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"\n👥 Total users in Azure SQL: {total_users}")
        
        # Check if courses table exists and has data
        if 'courses' in tables:
            cursor.execute("SELECT COUNT(*) FROM courses")
            total_courses = cursor.fetchone()[0]
            print(f"📚 Total courses in Azure SQL: {total_courses}")
            
            if total_courses == 0:
                print("⚠️  WARNING: No courses in Azure SQL database!")
        else:
            print("❌ CRITICAL: Courses table missing in Azure SQL!")
        
        # Check level settings
        if 'level_settings' in tables:
            cursor.execute("SELECT COUNT(*) FROM level_settings")
            level_count = cursor.fetchone()[0]
            print(f"🎯 Level settings in Azure SQL: {level_count}")
            
            if level_count == 0:
                print("⚠️  WARNING: No level settings in Azure SQL!")
        else:
            print("❌ CRITICAL: Level settings table missing in Azure SQL!")
        
        # Summary
        print(f"\n=== AZURE SQL DATABASE STATUS SUMMARY ===")
        
        issues = []
        if admin_count == 0:
            issues.append("Admin user missing")
        if total_users < 2:  # Should have admin + at least one regular user
            issues.append("Very few users (may need data migration)")
        if 'courses' not in tables:
            issues.append("Courses table missing")
        elif total_courses == 0:
            issues.append("No courses loaded")
        if 'level_settings' not in tables:
            issues.append("Level settings table missing")
        elif level_count == 0:
            issues.append("No level settings configured")
        
        if issues:
            print("⚠️  AZURE SQL DATABASE ISSUES FOUND:")
            for issue in issues:
                print(f"   - {issue}")
            print("\n🔧 RECOMMENDATIONS:")
            print("   1. Run data migration from local to Azure SQL")
            print("   2. Initialize missing tables and data")
            print("   3. Set up proper user accounts")
        else:
            print("✅ AZURE SQL DATABASE IS PROPERLY INITIALIZED")
        
        conn.close()
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Error connecting to Azure SQL Database: {e}")
        return False

if __name__ == "__main__":
    check_real_azure_database()
