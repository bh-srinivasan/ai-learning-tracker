#!/usr/bin/env python3
"""
Database migration script to add URL validation columns
"""
import sqlite3
import os

def migrate_database():
    """Add URL validation columns to courses table"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        print("   Please run the main application first to create the database.")
        return False
    
    print("🔄 Running database migration for URL validation...")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check current schema
        schema = conn.execute("PRAGMA table_info(courses)").fetchall()
        columns = [col['name'] for col in schema]
        
        print(f"📊 Current columns: {', '.join(columns)}")
        
        # Add new columns if they don't exist
        migrations = [
            ('url_status', 'ALTER TABLE courses ADD COLUMN url_status TEXT DEFAULT "unchecked"'),
            ('last_url_check', 'ALTER TABLE courses ADD COLUMN last_url_check TIMESTAMP')
        ]
        
        for column_name, sql in migrations:
            if column_name not in columns:
                print(f"   Adding column: {column_name}")
                conn.execute(sql)
            else:
                print(f"   ✅ Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify new schema
        schema = conn.execute("PRAGMA table_info(courses)").fetchall()
        new_columns = [col['name'] for col in schema]
        
        print(f"📊 Updated columns: {', '.join(new_columns)}")
        
        # Show some sample data
        print("\n📋 Sample course data:")
        sample_courses = conn.execute('''
            SELECT id, title, url, link, url_status, last_url_check
            FROM courses 
            WHERE (url IS NOT NULL AND url != '') 
               OR (link IS NOT NULL AND link != '')
            LIMIT 3
        ''').fetchall()
        
        for course in sample_courses:
            print(f"   ID {course['id']}: {course['title'][:40]}...")
            print(f"     URL: {course['url'] or course['link'] or 'None'}")
            print(f"     Status: {course['url_status']}")
            print(f"     Last Check: {course['last_url_check'] or 'Never'}")
            print()
        
        conn.close()
        
        print("✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🛠️  Course URL Validation Database Migration")
    print("=" * 60)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed! You can now:")
        print("   1. Run the test suite: python test_url_validation.py")
        print("   2. Start the Flask app and access Admin > URL Validation")
        print("   3. Run URL validation on your courses")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main()
