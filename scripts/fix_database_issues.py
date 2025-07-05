#!/usr/bin/env python3
"""
Fix Database Issues
1. Add missing URL column to courses table
2. Fix global learnings count logic
"""

import sqlite3
from dotenv import load_dotenv

def fix_database_issues():
    """Fix the identified database issues"""
    load_dotenv()
    
    print("🔧 AI Learning Tracker - Database Issue Fix")
    print("=" * 50)
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Issue 1: Fix courses table - add url column
    print("\n1️⃣ Fixing courses table structure...")
    
    # Check if url column exists
    cursor.execute("PRAGMA table_info(courses);")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'url' not in columns:
        try:
            # Add url column
            cursor.execute('ALTER TABLE courses ADD COLUMN url TEXT;')
            print("✅ Added 'url' column to courses table")
            
            # Copy data from link column to url column for existing records
            cursor.execute('UPDATE courses SET url = link WHERE url IS NULL;')
            print("✅ Copied existing link data to url column")
            
        except Exception as e:
            print(f"❌ Error adding url column: {e}")
    else:
        print("✅ URL column already exists")
    
    # Issue 2: Check global learnings count
    print("\n2️⃣ Analyzing global learnings count...")
    
    # Check current global learnings
    cursor.execute('SELECT COUNT(*) as count FROM learning_entries WHERE is_global = 1')
    global_count = cursor.fetchone()[0]
    print(f"📊 Current global learnings (is_global = 1): {global_count}")
    
    # Check all learning entries
    cursor.execute('SELECT COUNT(*) as count FROM learning_entries')
    total_count = cursor.fetchone()[0]
    print(f"📊 Total learning entries: {total_count}")
    
    # Check entries without user_id (potential global entries)
    cursor.execute('SELECT COUNT(*) as count FROM learning_entries WHERE user_id IS NULL OR user_id = 0')
    null_user_count = cursor.fetchone()[0]
    print(f"📊 Entries without user_id: {null_user_count}")
    
    # Check sample data
    cursor.execute('SELECT id, title, user_id, is_global FROM learning_entries LIMIT 5')
    sample_entries = cursor.fetchall()
    print(f"\n📋 Sample learning entries:")
    for entry in sample_entries:
        print(f"   ID: {entry[0]}, Title: {entry[1][:30]}..., User ID: {entry[2]}, Is Global: {entry[3]}")
    
    # Issue 3: Add missing columns to courses table if needed
    print("\n3️⃣ Checking for other missing columns...")
    
    missing_columns = []
    expected_columns = {
        'category': 'TEXT',
        'difficulty': 'TEXT'
    }
    
    for col_name, col_type in expected_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE courses ADD COLUMN {col_name} {col_type};')
                print(f"✅ Added '{col_name}' column to courses table")
                missing_columns.append(col_name)
            except Exception as e:
                print(f"❌ Error adding {col_name} column: {e}")
    
    # Update existing courses with default values for new columns
    if missing_columns:
        try:
            if 'category' in missing_columns:
                cursor.execute("UPDATE courses SET category = 'AI/ML' WHERE category IS NULL;")
                print("✅ Set default category for existing courses")
            
            if 'difficulty' in missing_columns:
                cursor.execute("UPDATE courses SET difficulty = level WHERE difficulty IS NULL;")
                print("✅ Set difficulty based on level for existing courses")
        except Exception as e:
            print(f"❌ Error updating default values: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 Database fixes completed!")
    print("\n💡 Next Steps:")
    print("   1. Test LinkedIn course addition")
    print("   2. Check admin dashboard global learnings count")
    print("   3. Restart Flask application")

def test_linkedin_course_insertion():
    """Test if LinkedIn course insertion works now"""
    print("\n🧪 Testing LinkedIn Course Insertion")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Test course data
        test_course = {
            'title': 'Test LinkedIn Course',
            'source': 'LinkedIn Learning',
            'level': 'Beginner',
            'link': 'https://www.linkedin.com/learning/test-course',
            'url': 'https://www.linkedin.com/learning/test-course',
            'points': 50,
            'description': 'Test course for database fix validation',
            'category': 'AI/ML',
            'difficulty': 'Beginner'
        }
        
        # Try to insert with all columns
        cursor.execute('''
            INSERT INTO courses (title, source, level, link, url, points, description, category, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_course['title'], test_course['source'], test_course['level'], 
              test_course['link'], test_course['url'], test_course['points'], 
              test_course['description'], test_course['category'], test_course['difficulty']))
        
        conn.commit()
        print("✅ Test course insertion successful!")
        
        # Clean up test data
        cursor.execute("DELETE FROM courses WHERE title = 'Test LinkedIn Course'")
        conn.commit()
        print("✅ Test data cleaned up")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test insertion failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_database_issues()
    test_linkedin_course_insertion()
