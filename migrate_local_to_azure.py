#!/usr/bin/env python3
"""
Local to Azure Database Migration Tool
Migrates all data from local SQLite to Azure SQL Database
"""

import sqlite3
import pyodbc
import os
from datetime import datetime

def get_azure_connection():
    """Get Azure SQL connection"""
    server = os.getenv('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
    database = os.getenv('AZURE_SQL_DATABASE', 'ai-learning-db')
    username = os.getenv('AZURE_SQL_USERNAME', 'bharath')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    if not password:
        raise ValueError("AZURE_SQL_PASSWORD environment variable not set")
    
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    return pyodbc.connect(connection_string)

def analyze_local_database():
    """Analyze local database structure and data"""
    if not os.path.exists('ai_learning.db'):
        print("❌ Local database 'ai_learning.db' not found")
        return None
    
    print("🔍 ANALYZING LOCAL DATABASE")
    print("=" * 50)
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_data = {}
    total_rows = 0
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_rows += count
        
        print(f"📋 Table: {table_name} - {count} rows")
        
        if count > 0:
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            data = cursor.fetchall()
            
            table_data[table_name] = {
                'columns': columns,
                'data': data,
                'count': count
            }
            
            # Show sample
            print(f"   📝 Columns: {', '.join(columns)}")
            if data:
                print(f"   🔍 Sample: {data[0]}")
    
    conn.close()
    print(f"\n📊 Total rows to migrate: {total_rows}")
    return table_data

def clear_azure_data(azure_conn):
    """Clear existing data from Azure SQL (except sample data)"""
    print("\n🧹 CLEARING EXISTING AZURE DATA")
    print("=" * 50)
    
    cursor = azure_conn.cursor()
    
    # Tables to clear (in dependency order)
    tables_to_clear = [
        'admin_actions',
        'points_log', 
        'security_events',
        'security_logs',
        'session_activity',
        'sessions',
        'user_sessions',
        'user_courses',
        'user_personal_courses',
        'learning_entries',
        'users',
        'courses',
        'course_search_configs',
        'level_settings'
    ]
    
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✅ Cleared table: {table}")
        except Exception as e:
            print(f"⚠️  Could not clear {table}: {e}")
    
    azure_conn.commit()
    print("🧹 Azure database cleared")

def migrate_table_data(local_data, azure_conn, table_name):
    """Migrate data for a specific table"""
    if table_name not in local_data:
        print(f"⚠️  No local data for table: {table_name}")
        return 0
    
    table_info = local_data[table_name]
    columns = table_info['columns']
    data = table_info['data']
    
    if not data:
        print(f"📭 No data to migrate for table: {table_name}")
        return 0
    
    cursor = azure_conn.cursor()
    
    # Create parameterized insert statement
    placeholders = ', '.join(['?' for _ in columns])
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    try:
        # Insert data in batches
        migrated_count = 0
        for row in data:
            try:
                cursor.execute(insert_sql, row)
                migrated_count += 1
            except Exception as e:
                print(f"⚠️  Error inserting row in {table_name}: {e}")
                print(f"   Row data: {row}")
        
        azure_conn.commit()
        print(f"✅ Migrated {migrated_count}/{len(data)} rows to table: {table_name}")
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error migrating table {table_name}: {e}")
        azure_conn.rollback()
        return 0

def migrate_all_data():
    """Main migration function"""
    print("🚀 LOCAL TO AZURE DATABASE MIGRATION")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print("=" * 60)
    
    # Step 1: Analyze local database
    local_data = analyze_local_database()
    if not local_data:
        print("❌ Migration aborted - no local data found")
        return
    
    # Step 2: Connect to Azure
    try:
        azure_conn = get_azure_connection()
        print("✅ Connected to Azure SQL Database")
    except Exception as e:
        print(f"❌ Failed to connect to Azure SQL: {e}")
        return
    
    # Step 3: Clear Azure data (ask for confirmation)
    print(f"\n⚠️  WARNING: This will delete all existing data in Azure SQL!")
    print("   Current Azure data will be replaced with local data.")
    response = input("Continue? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Migration cancelled by user")
        azure_conn.close()
        return
    
    clear_azure_data(azure_conn)
    
    # Step 4: Migrate data (in dependency order)
    migration_order = [
        'level_settings',
        'users', 
        'courses',
        'course_search_configs',
        'learning_entries',
        'user_courses',
        'user_personal_courses',
        'points_log',
        'security_events', 
        'security_logs',
        'admin_actions',
        'sessions',
        'user_sessions',
        'session_activity'
    ]
    
    print("\n📦 MIGRATING DATA TO AZURE")
    print("=" * 50)
    
    total_migrated = 0
    for table_name in migration_order:
        migrated = migrate_table_data(local_data, azure_conn, table_name)
        total_migrated += migrated
    
    # Migrate any remaining tables not in the ordered list
    for table_name in local_data:
        if table_name not in migration_order:
            migrated = migrate_table_data(local_data, azure_conn, table_name)
            total_migrated += migrated
    
    azure_conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 MIGRATION COMPLETED!")
    print(f"📊 Total rows migrated: {total_migrated}")
    print(f"⏰ Completed at: {datetime.now()}")
    print("=" * 60)
    
    print("\n🔍 Next steps:")
    print("1. Run 'python check_real_azure_sql.py' to verify migration")
    print("2. Test login with migrated user accounts")
    print("3. Verify all functionality works with Azure data")

if __name__ == "__main__":
    migrate_all_data()
