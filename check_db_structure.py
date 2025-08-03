#!/usr/bin/env python3
"""
Azure Database Structure Verification Tool
ONLY checks Azure database - NO LOCAL CHECKING
"""

from database_manager import get_db_connection

def check_azure_database():
    """Check Azure database structure using existing connection"""
    print("🔍 AZURE DATABASE STRUCTURE VERIFICATION")
    print("=" * 50)
    print("⚠️  AZURE DATABASE ONLY - LOCAL COMPLETELY IGNORED")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_info = {}
        
        print(f"📊 Found {len(tables)} tables in Azure database:")
        
        for table in tables:
            table_name = table[0]
            print(f"\n🔍 Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            table_info[table_name] = {
                'columns': columns,
                'count': 0
            }
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            table_info[table_name]['count'] = count
            
            print(f"   📈 Row count: {count}")
            print("   📋 Columns:")
            for col in columns:
                print(f"      - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
        
        conn.close()
        return table_info
        
    except Exception as e:
        print(f"❌ Error checking Azure database: {e}")
        return {}

if __name__ == "__main__":
    print("🔍 Azure Database Structure Verification Tool")
    print("=" * 50)
    
    # Check ONLY Azure database
    azure_info = check_azure_database()
    
    if azure_info:
        print("\n✅ AZURE DATABASE VERIFICATION COMPLETE")
        print(f"✅ Found {len(azure_info)} tables in Azure database")
        
        # Check for critical tables
        critical_tables = ['users', 'courses', 'level_settings']
        missing_critical = []
        
        for table in critical_tables:
            if table not in azure_info:
                missing_critical.append(table)
        
        if missing_critical:
            print(f"❌ MISSING CRITICAL TABLES: {missing_critical}")
        else:
            print("✅ All critical tables present in Azure")
    else:
        print("\n❌ Could not access Azure database")
