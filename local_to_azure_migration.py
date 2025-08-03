#!/usr/bin/env python3
"""
Local to Azure SQL Database Migration Tool
Migrates all data from local SQLite to Azure SQL Server
"""

import sqlite3
import pyodbc
import os
from datetime import datetime
from werkzeug.security import check_password_hash

def get_azure_connection():
    """Get Azure SQL connection using environment variables"""
    try:
        server = os.getenv('AZURE_SQL_SERVER')
        database = os.getenv('AZURE_SQL_DATABASE') 
        username = os.getenv('AZURE_SQL_USERNAME')
        password = os.getenv('AZURE_SQL_PASSWORD')
        
        if not all([server, database, username, password]):
            raise ValueError("Missing Azure SQL environment variables")
        
        connection_string = f"""
        DRIVER={{ODBC Driver 17 for SQL Server}};
        SERVER={server};
        DATABASE={database};
        UID={username};
        PWD={password};
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
        """
        
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"❌ Azure SQL connection error: {e}")
        return None

def get_local_connection():
    """Get local SQLite connection"""
    try:
        if not os.path.exists('ai_learning.db'):
            print("❌ Local database 'ai_learning.db' not found")
            return None
        
        conn = sqlite3.connect('ai_learning.db')
        return conn
    except Exception as e:
        print(f"❌ Local SQLite connection error: {e}")
        return None

def analyze_local_data():
    """Analyze what data exists in local database"""
    print("🔍 ANALYZING LOCAL DATABASE")
    print("=" * 50)
    
    conn = get_local_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        table_data = {}
        total_rows = 0
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_rows += count
            
            table_data[table_name] = count
            print(f"   📋 {table_name}: {count} rows")
            
            # Show sample data for important tables
            if count > 0 and table_name in ['users', 'courses', 'learning_entries']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
                sample = cursor.fetchall()
                if sample:
                    print(f"      Sample: {sample[0]}")
        
        print(f"\n📊 Total rows in local database: {total_rows}")
        conn.close()
        return table_data
        
    except Exception as e:
        print(f"❌ Error analyzing local data: {e}")
        conn.close()
        return {}

def migrate_table_data(local_cursor, azure_cursor, table_name):
    """Migrate data from local table to Azure table"""
    try:
        print(f"🔄 Migrating table: {table_name}")
        
        # Get local data
        local_cursor.execute(f"SELECT * FROM {table_name}")
        local_data = local_cursor.fetchall()
        
        if not local_data:
            print(f"   ⚠️  No data in local {table_name}")
            return True
        
        print(f"   📊 Found {len(local_data)} rows in local {table_name}")
        
        # Get column names from local table
        local_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = local_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Check if data already exists in Azure
        azure_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        azure_count = azure_cursor.fetchone()[0]
        
        if azure_count > 0:
            print(f"   ⚠️  Azure {table_name} already has {azure_count} rows")
            choice = input(f"   🤔 Replace data in Azure {table_name}? (y/N): ").strip().lower()
            if choice != 'y':
                print(f"   ⏭️  Skipping {table_name}")
                return True
            
            # Clear existing data (except for critical system tables)
            if table_name == 'users':
                azure_cursor.execute("SELECT username FROM users")
                existing_users = [row[0] for row in azure_cursor.fetchall()]
                print(f"   ⚠️  Existing users in Azure: {existing_users}")
                confirm = input("   🚨 CONFIRM: Delete ALL existing users and migrate from local? (type 'CONFIRM'): ")
                if confirm != 'CONFIRM':
                    print(f"   ❌ Skipping {table_name} - user cancelled")
                    return True
            
            azure_cursor.execute(f"DELETE FROM {table_name}")
            print(f"   🗑️  Cleared existing data from Azure {table_name}")
        
        # Prepare insert statement
        placeholders = ', '.join(['?' for _ in column_names])
        columns_str = ', '.join(column_names)
        
        # Handle identity columns by setting IDENTITY_INSERT if needed
        identity_tables = ['users', 'courses', 'learning_entries', 'level_settings', 'points_log', 'security_events', 'security_logs']
        if table_name in identity_tables:
            try:
                azure_cursor.execute(f"SET IDENTITY_INSERT {table_name} ON")
            except:
                pass  # Continue if IDENTITY_INSERT fails
        
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insert data row by row for better error handling
        migrated_count = 0
        for row in local_data:
            try:
                # Convert data types if needed
                converted_row = []
                for i, value in enumerate(row):
                    # Handle datetime conversion and None values
                    if value is None:
                        converted_row.append(None)
                    elif isinstance(value, str) and ('date' in column_names[i].lower() or 'time' in column_names[i].lower()):
                        # Try to parse datetime strings
                        try:
                            # Handle various datetime formats
                            if 'T' in value or '-' in value:
                                converted_row.append(value)
                            else:
                                converted_row.append(value)
                        except:
                            converted_row.append(value)
                    else:
                        converted_row.append(value)
                
                azure_cursor.execute(insert_sql, converted_row)
                migrated_count += 1
            except Exception as e:
                print(f"   ⚠️  Error inserting row {migrated_count + 1}: {e}")
                print(f"   📝 Row data: {row}")
                continue
        
        # Turn off IDENTITY_INSERT
        if table_name in identity_tables:
            try:
                azure_cursor.execute(f"SET IDENTITY_INSERT {table_name} OFF")
            except:
                pass
        
        print(f"   ✅ Successfully migrated {migrated_count}/{len(local_data)} rows to Azure {table_name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error migrating {table_name}: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 LOCAL TO AZURE SQL DATABASE MIGRATION")
    print("=" * 60)
    
    # First analyze local data
    local_data = analyze_local_data()
    if not local_data:
        print("❌ No local data found to migrate")
        return
    
    # Get connections
    print("\n📡 Establishing connections...")
    local_conn = get_local_connection()
    if not local_conn:
        return
    
    azure_conn = get_azure_connection()
    if not azure_conn:
        local_conn.close()
        return
    
    try:
        local_cursor = local_conn.cursor()
        azure_cursor = azure_conn.cursor()
        
        # Get Azure tables
        azure_cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        azure_tables = [row[0] for row in azure_cursor.fetchall()]
        
        print(f"📊 Found {len(azure_tables)} tables in Azure database")
        
        # Find common tables that have data in local
        tables_with_data = [table for table, count in local_data.items() if count > 0]
        common_tables = [table for table in tables_with_data if table in azure_tables]
        
        print(f"\n🔄 Tables to migrate (with local data): {', '.join(common_tables)}")
        
        if not common_tables:
            print("❌ No common tables with data found")
            return
        
        # Define migration order (dependencies first)
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
            'session_activity',
            'user_sessions',
            'sessions',
            'admin_actions'
        ]
        
        # Filter to only existing tables with data
        tables_to_migrate = [table for table in migration_order if table in common_tables]
        
        # Add any remaining common tables not in the order
        for table in common_tables:
            if table not in tables_to_migrate:
                tables_to_migrate.append(table)
        
        print(f"\n🎯 Migration order: {' → '.join(tables_to_migrate)}")
        
        # Show summary
        print(f"\n📋 MIGRATION SUMMARY:")
        for table in tables_to_migrate:
            print(f"   📊 {table}: {local_data[table]} rows")
        
        # Confirm migration
        print(f"\n⚠️  WARNING: This will migrate data from local SQLite to Azure SQL")
        print(f"⚠️  Existing Azure data may be replaced for some tables")
        confirm = input("\n🤔 Continue with migration? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Migration cancelled by user")
            return
        
        # Perform migration
        print(f"\n🚀 Starting migration...")
        successful_migrations = 0
        failed_migrations = 0
        
        for table in tables_to_migrate:
            print(f"\n{'='*50}")
            success = migrate_table_data(local_cursor, azure_cursor, table)
            if success:
                successful_migrations += 1
                azure_conn.commit()  # Commit after each successful table
            else:
                failed_migrations += 1
                try:
                    azure_conn.rollback()  # Rollback failed table
                except:
                    pass
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"🎉 MIGRATION COMPLETE!")
        print(f"✅ Successful: {successful_migrations} tables")
        print(f"❌ Failed: {failed_migrations} tables")
        
        if successful_migrations > 0:
            print(f"\n🔍 Verifying migration...")
            for table in tables_to_migrate:
                try:
                    local_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    local_count = local_cursor.fetchone()[0]
                    
                    azure_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    azure_count = azure_cursor.fetchone()[0]
                    status = "✅" if local_count == azure_count else "⚠️"
                    print(f"   {status} {table}: Local={local_count}, Azure={azure_count}")
                except Exception as e:
                    print(f"   ❌ {table}: Could not verify - {e}")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        try:
            azure_conn.rollback()
        except:
            pass
    
    finally:
        local_conn.close()
        azure_conn.close()
        print(f"\n🔌 Connections closed")

if __name__ == "__main__":
    main()
