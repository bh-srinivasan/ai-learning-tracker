#!/usr/bin/env python3
"""
Azure SQL Database Initialization Script
Initializes Azure SQL Database with one row of sample data in each table
"""

import os
import pyodbc
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def initialize_azure_database():
    """Initialize Azure SQL Database with sample data"""
    print("🚀 AZURE SQL DATABASE INITIALIZATION")
    print("=" * 60)
    print("⚠️  INITIALIZING AZURE SQL WITH SAMPLE DATA")
    print("=" * 60)
    
    # Azure SQL connection details
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USERNAME')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
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
        
        # Check current state
        cursor.execute("SELECT COUNT(*) FROM users")
        existing_users = cursor.fetchone()[0]
        print(f"📊 Current users in Azure SQL: {existing_users}")
        
        if existing_users > 1:
            print("⚠️  Database already has multiple users. Skipping initialization.")
            conn.close()
            return
        
        print("\n🔧 Initializing tables with sample data...")
        
        # 1. Initialize level_settings first (referenced by other tables)
        print("\n1️⃣ Initializing level_settings...")
        cursor.execute("SELECT COUNT(*) FROM level_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO level_settings (level_name, points_required, created_at)
                VALUES (?, ?, ?)
            """, ('Beginner', 0, datetime.now()))
            print("   ✅ Added Beginner level setting")
        else:
            print("   ℹ️  Level settings already exist")
        
        # 2. Ensure admin user exists or create demo user
        print("\n2️⃣ Checking users table...")
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'demo'")
        demo_exists = cursor.fetchone()[0] > 0
        
        if not demo_exists:
            demo_password_hash = generate_password_hash('demo123')
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, level, created_at, points, status, 
                    user_selected_level, login_count, level_points
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'demo', demo_password_hash, 'Beginner', datetime.now(), 
                0, 'active', 'Beginner', 0, 0
            ))
            print("   ✅ Added demo user")
        else:
            print("   ℹ️  Demo user already exists")
        
        # Get user ID for foreign key references
        cursor.execute("SELECT TOP 1 id FROM users ORDER BY id")
        user_id = cursor.fetchone()[0]
        
        # 3. Initialize courses
        print("\n3️⃣ Initializing courses...")
        cursor.execute("SELECT COUNT(*) FROM courses")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO courses (
                    title, source, level, link, created_at, points, 
                    description, url, category, difficulty, url_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Introduction to AI Learning',
                'Microsoft Learn',
                'Beginner',
                'https://learn.microsoft.com/ai-fundamentals',
                datetime.now(),
                50,
                'Learn the fundamentals of artificial intelligence',
                'https://learn.microsoft.com/ai-fundamentals',
                'AI Fundamentals',
                'Beginner',
                'active'
            ))
            print("   ✅ Added sample course")
        else:
            print("   ℹ️  Courses already exist")
        
        # Get course ID for foreign key references
        cursor.execute("SELECT TOP 1 id FROM courses ORDER BY id")
        course_result = cursor.fetchone()
        course_id = course_result[0] if course_result else None
        
        # 4. Initialize learning_entries
        print("\n4️⃣ Initializing learning_entries...")
        cursor.execute("SELECT COUNT(*) FROM learning_entries")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO learning_entries (
                    user_id, title, description, date_added, tags, is_global
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                'My First Learning Entry',
                'Started learning about AI and machine learning fundamentals',
                datetime.now(),
                'AI,Learning,Fundamentals',
                0
            ))
            print("   ✅ Added sample learning entry")
        else:
            print("   ℹ️  Learning entries already exist")
        
        # 5. Initialize user_courses (if course exists)
        if course_id:
            print("\n5️⃣ Initializing user_courses...")
            cursor.execute("SELECT COUNT(*) FROM user_courses")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO user_courses (user_id, course_id, completed, completion_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, course_id, 0, None))
                print("   ✅ Added user-course association")
            else:
                print("   ℹ️  User-courses already exist")
        
        # 6. Initialize course_search_configs
        print("\n6️⃣ Initializing course_search_configs...")
        cursor.execute("SELECT COUNT(*) FROM course_search_configs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO course_search_configs (
                    topic_name, search_keywords, source, is_active, created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                'AI Fundamentals',
                'artificial intelligence,machine learning,AI basics',
                'Microsoft Learn',
                1,
                datetime.now()
            ))
            print("   ✅ Added course search config")
        else:
            print("   ℹ️  Course search configs already exist")
        
        # 7. Initialize user_personal_courses
        print("\n7️⃣ Initializing user_personal_courses...")
        cursor.execute("SELECT COUNT(*) FROM user_personal_courses")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO user_personal_courses (
                    user_id, title, source, course_url, description, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                'Personal AI Study Course',
                'Self-Study',
                'https://example.com/personal-ai-course',
                'My personal collection of AI learning resources',
                datetime.now()
            ))
            print("   ✅ Added personal course")
        else:
            print("   ℹ️  Personal courses already exist")
        
        # 8. Initialize user_sessions
        print("\n8️⃣ Initializing user_sessions...")
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        if cursor.fetchone()[0] == 0:
            session_token = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute("""
                INSERT INTO user_sessions (
                    user_id, session_token, created_at, expires_at, ip_address, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session_token,
                datetime.now(),
                datetime.now() + timedelta(hours=24),
                '127.0.0.1',
                1
            ))
            print("   ✅ Added user session")
        else:
            print("   ℹ️  User sessions already exist")
        
        # 9. Initialize session_activity
        print("\n9️⃣ Initializing session_activity...")
        cursor.execute("SELECT COUNT(*) FROM session_activity")
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT TOP 1 session_token FROM user_sessions ORDER BY id DESC")
            session_token_result = cursor.fetchone()
            if session_token_result:
                cursor.execute("""
                    INSERT INTO session_activity (
                        session_token, activity_type, activity_data, timestamp, ip_address
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_token_result[0],
                    'login',
                    'User logged in successfully',
                    datetime.now(),
                    '127.0.0.1'
                ))
                print("   ✅ Added session activity")
            else:
                print("   ⚠️  No session token found, skipping session activity")
        else:
            print("   ℹ️  Session activity already exists")
        
        # 10. Initialize points_log (if course exists)
        if course_id:
            print("\n🔟 Initializing points_log...")
            cursor.execute("SELECT COUNT(*) FROM points_log")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO points_log (
                        user_id, course_id, action, points_change, points_before, 
                        points_after, reason, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    course_id,
                    'course_enrollment',
                    10,
                    0,
                    10,
                    'Points awarded for enrolling in course',
                    datetime.now()
                ))
                print("   ✅ Added points log entry")
            else:
                print("   ℹ️  Points log already exists")
        
        # 11. Initialize security_events
        print("\n1️⃣1️⃣ Initializing security_events...")
        cursor.execute("SELECT COUNT(*) FROM security_events")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO security_events (
                    event_type, details, ip_address, user_id, timestamp
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                'login_success',
                'Demo user login successful',
                '127.0.0.1',
                user_id,
                datetime.now()
            ))
            print("   ✅ Added security event")
        else:
            print("   ℹ️  Security events already exist")
        
        # 12. Initialize security_logs
        print("\n1️⃣2️⃣ Initializing security_logs...")
        cursor.execute("SELECT COUNT(*) FROM security_logs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO security_logs (
                    event_type, description, ip_address, user_id, timestamp, success
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'authentication',
                'Demo user authentication attempt',
                '127.0.0.1',
                user_id,
                datetime.now(),
                1
            ))
            print("   ✅ Added security log")
        else:
            print("   ℹ️  Security logs already exist")
        
        # Commit all changes
        conn.commit()
        
        # Verify initialization
        print(f"\n=== AZURE SQL INITIALIZATION VERIFICATION ===")
        
        tables_to_check = [
            'users', 'courses', 'level_settings', 'learning_entries',
            'user_courses', 'course_search_configs', 'user_personal_courses',
            'user_sessions', 'session_activity', 'points_log',
            'security_events', 'security_logs'
        ]
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {table}: {count} rows")
        
        conn.close()
        
        print(f"\n✅ AZURE SQL DATABASE INITIALIZATION COMPLETE!")
        print(f"✅ All tables now have at least one row of sample data")
        print(f"\n🔐 Test Credentials:")
        print(f"   Username: demo")
        print(f"   Password: demo123")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Azure SQL Database: {e}")
        return False

if __name__ == "__main__":
    initialize_azure_database()
