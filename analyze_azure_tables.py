#!/usr/bin/env python3
"""
Azure Database Detailed Table Analysis
Shows detailed structure of each table in Azure database ONLY
"""

from database_manager import get_db_connection

def analyze_azure_table_structures():
    """Detailed analysis of each table structure in Azure database"""
    print("🔍 AZURE DATABASE - DETAILED TABLE ANALYSIS")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        print(f"📊 Analyzing {len(tables)} tables in Azure database\n")
        
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            
            print(f"{i}. 🔍 TABLE: {table_name}")
            print("-" * 40)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            print(f"📊 Total Rows: {count}")
            print(f"📋 Total Columns: {len(columns)}")
            
            # Show detailed column structure
            print("🏗️  Column Structure:")
            for col in columns:
                col_id, name, data_type, not_null, default_val, is_pk = col
                
                # Format column info
                constraints = []
                if is_pk:
                    constraints.append("PRIMARY KEY")
                if not_null:
                    constraints.append("NOT NULL")
                if default_val is not None:
                    constraints.append(f"DEFAULT {default_val}")
                
                constraint_str = " " + " ".join(constraints) if constraints else ""
                print(f"   {col_id + 1:2d}. {name:<20} {data_type:<12}{constraint_str}")
            
            # Show sample data for important tables
            if table_name in ['users', 'courses', 'level_settings'] and count > 0:
                print("📝 Sample Data:")
                
                if table_name == 'users':
                    cursor.execute("""
                        SELECT id, username, level, points, status, login_count 
                        FROM users 
                        ORDER BY id 
                        LIMIT 5
                    """)
                elif table_name == 'courses':
                    cursor.execute("""
                        SELECT id, title, source, level, points 
                        FROM courses 
                        ORDER BY id 
                        LIMIT 3
                    """)
                elif table_name == 'level_settings':
                    cursor.execute("""
                        SELECT level_name, points_required 
                        FROM level_settings 
                        ORDER BY points_required
                    """)
                
                sample_data = cursor.fetchall()
                if sample_data:
                    for row in sample_data:
                        print(f"   {row}")
            
            # Show foreign key relationships
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print("🔗 Foreign Key Relationships:")
                for fk in foreign_keys:
                    print(f"   {fk[3]} -> {fk[2]}.{fk[4]}")
            
            # Show indexes
            cursor.execute(f"PRAGMA index_list({table_name});")
            indexes = cursor.fetchall()
            
            if indexes:
                print("📇 Indexes:")
                for idx in indexes:
                    print(f"   {idx[1]} ({'UNIQUE' if idx[2] else 'NON-UNIQUE'})")
            
            print()  # Empty line between tables
        
        # Summary of critical data
        print("=" * 60)
        print("🎯 AZURE DATABASE CRITICAL DATA SUMMARY")
        print("=" * 60)
        
        # Users summary
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active' OR status IS NULL")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()[0] > 0
        
        print(f"👥 Users: {total_users} total, {active_users} active, Admin: {'✅ Yes' if admin_exists else '❌ No'}")
        
        # Courses summary
        cursor.execute("SELECT COUNT(*) FROM courses")
        total_courses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT level) FROM courses")
        course_levels = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT source) FROM courses")
        course_sources = cursor.fetchone()[0]
        
        print(f"📚 Courses: {total_courses} total, {course_levels} levels, {course_sources} sources")
        
        # Level settings summary
        cursor.execute("SELECT level_name, points_required FROM level_settings ORDER BY points_required")
        levels = cursor.fetchall()
        
        print("🎯 Level Settings:")
        for level in levels:
            print(f"   {level[0]}: {level[1]} points required")
        
        # Session activity
        cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1 OR is_active IS NULL")
        active_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM session_activity")
        total_activity = cursor.fetchone()[0]
        
        print(f"🔐 Sessions: {active_sessions} active sessions, {total_activity} activity records")
        
        conn.close()
        
        print("\n✅ Azure database structure analysis complete!")
        
    except Exception as e:
        print(f"❌ Error analyzing Azure database: {e}")

if __name__ == "__main__":
    analyze_azure_table_structures()
