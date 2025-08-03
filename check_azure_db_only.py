#!/usr/bin/env python3
"""
Azure Database Structure Verification Tool
ONLY checks Azure database - ignores local completely
"""

from database_manager import get_db_connection

def check_azure_database_only():
    """Check ONLY Azure database structure and initialization"""
    print("🔍 AZURE DATABASE VERIFICATION")
    print("=" * 50)
    print("⚠️  NOTE: This tool ONLY checks Azure database")
    print("⚠️  Local database is completely IGNORED per user request")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables in Azure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📊 AZURE DATABASE: Found {len(tables)} tables")
        
        # Define expected core tables for the application
        expected_tables = {
            'users': 'Core user accounts',
            'learning_entries': 'User learning records',
            'courses': 'Available courses',
            'user_courses': 'User-course associations',
            'level_settings': 'Level configuration',
            'user_sessions': 'Active user sessions',
            'session_activity': 'Session tracking',
            'security_events': 'Security audit log',
            'points_log': 'Points tracking',
            'course_search_configs': 'Course search settings',
            'user_personal_courses': 'User custom courses',
            'excel_upload_reports': 'Excel upload tracking',
            'excel_upload_row_details': 'Excel upload details'
        }
        
        table_status = {}
        
        for table in tables:
            table_name = table[0]
            print(f"\n🔍 AZURE TABLE: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            table_status[table_name] = {
                'columns': len(columns),
                'rows': count,
                'is_expected': table_name in expected_tables
            }
            
            status_icon = "✅" if table_name in expected_tables else "ℹ️"
            description = expected_tables.get(table_name, "Additional table")
            
            print(f"   {status_icon} {description}")
            print(f"   📊 Columns: {len(columns)}, Rows: {count}")
            
            if count == 0 and table_name in ['users', 'courses', 'level_settings']:
                print(f"   ⚠️  WARNING: Critical table '{table_name}' is EMPTY!")
            
            # Show columns for critical tables
            if table_name in ['users', 'courses', 'level_settings']:
                print("   📋 Schema:")
                for col in columns:
                    null_status = "NOT NULL" if col[3] else "NULL"
                    pk_status = "PRIMARY KEY" if col[5] else ""
                    print(f"      - {col[1]} ({col[2]}) {null_status} {pk_status}")
        
        # Check for missing expected tables
        existing_tables = set(table[0] for table in tables)
        missing_tables = set(expected_tables.keys()) - existing_tables
        
        print(f"\n=== AZURE DATABASE ANALYSIS ===")
        
        if missing_tables:
            print(f"❌ MISSING CRITICAL TABLES in Azure:")
            for table in missing_tables:
                print(f"   - {table}: {expected_tables[table]}")
        else:
            print("✅ All expected tables present in Azure")
        
        # Check critical data
        print(f"\n=== CRITICAL DATA CHECK (Azure) ===")
        
        # Check admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print("✅ Admin user exists in Azure")
            
            # Get admin details
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
            print("❌ Admin user MISSING in Azure - CRITICAL ISSUE!")
        
        # Check total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"📊 Total users in Azure: {total_users}")
        
        # Check courses
        cursor.execute("SELECT COUNT(*) FROM courses")
        total_courses = cursor.fetchone()[0]
        print(f"📚 Total courses in Azure: {total_courses}")
        
        # Check level settings
        cursor.execute("SELECT COUNT(*) FROM level_settings")
        level_count = cursor.fetchone()[0]
        print(f"🎯 Level settings in Azure: {level_count}")
        
        if level_count == 0:
            print("⚠️  WARNING: No level settings configured!")
        
        # Final status
        print(f"\n=== AZURE DATABASE STATUS ===")
        
        critical_issues = []
        if admin_count == 0:
            critical_issues.append("Admin user missing")
        if total_users == 0:
            critical_issues.append("No users in database")
        if level_count == 0:
            critical_issues.append("Level settings not configured")
        if missing_tables:
            critical_issues.append(f"{len(missing_tables)} critical tables missing")
        
        if critical_issues:
            print("❌ AZURE DATABASE HAS CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"   - {issue}")
            print("\n🔧 RECOMMENDATION: Run Azure database initialization")
        else:
            print("✅ AZURE DATABASE IS PROPERLY INITIALIZED")
            print("✅ All critical tables and data present")
            print("✅ Admin user configured and functional")
        
        conn.close()
        return len(critical_issues) == 0
        
    except Exception as e:
        print(f"❌ ERROR accessing Azure database: {e}")
        print("🔧 Check Azure database connectivity and permissions")
        return False

if __name__ == "__main__":
    check_azure_database_only()
