#!/usr/bin/env python3
"""
Fix Existing Admin Entries to be Global
Update existing admin-created entries to have is_global = 1
"""

import sqlite3
from dotenv import load_dotenv

def fix_existing_admin_entries():
    """Fix existing admin entries to be global"""
    load_dotenv()
    
    print("🔧 Fixing Existing Admin Learning Entries")
    print("=" * 45)
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Find admin user entries that should be global
    cursor.execute('''
        SELECT le.id, le.title, le.is_global, u.username
        FROM learning_entries le
        JOIN users u ON le.user_id = u.id
        WHERE u.username = 'admin' AND le.is_global = 0
    ''')
    
    admin_entries = cursor.fetchall()
    
    print(f"📋 Found {len(admin_entries)} admin entries that should be global:")
    for entry in admin_entries:
        print(f"   ID: {entry[0]}, Title: {entry[1][:40]}..., Currently Global: {entry[2]}")
    
    if admin_entries:
        try:
            # Update admin entries to be global
            cursor.execute('''
                UPDATE learning_entries 
                SET is_global = 1 
                WHERE user_id = (SELECT id FROM users WHERE username = 'admin')
                AND is_global = 0
            ''')
            
            updated_count = cursor.rowcount
            conn.commit()
            
            print(f"\n✅ Updated {updated_count} admin entries to be global")
            
            # Verify the new count
            cursor.execute('SELECT COUNT(*) FROM learning_entries WHERE is_global = 1')
            new_global_count = cursor.fetchone()[0]
            print(f"📊 New global learnings count: {new_global_count}")
            
        except Exception as e:
            print(f"❌ Error updating entries: {e}")
            conn.rollback()
    else:
        print("ℹ️  No admin entries need to be updated")
    
    conn.close()

def verify_fix():
    """Verify that the fixes are working"""
    print(f"\n🔍 Verifying Fixes")
    print("=" * 20)
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Check courses table structure
    cursor.execute("PRAGMA table_info(courses);")
    courses_columns = [col[1] for col in cursor.fetchall()]
    
    print("📋 Courses table columns:")
    missing_columns = []
    expected_columns = ['url', 'category', 'difficulty']
    for col in expected_columns:
        if col in courses_columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} (missing)")
            missing_columns.append(col)
    
    # Check global learnings count
    cursor.execute('SELECT COUNT(*) FROM learning_entries WHERE is_global = 1')
    global_count = cursor.fetchone()[0]
    print(f"\n📊 Global learnings count: {global_count}")
    
    # Test course insertion capability
    print(f"\n🧪 Testing course insertion...")
    try:
        # Try a simple insert to verify structure
        cursor.execute('''
            INSERT INTO courses (title, source, level, link, url, points, description, category, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Course', 'Test Source', 'Beginner', 'http://test.com', 'http://test.com', 
              50, 'Test Description', 'Test Category', 'Beginner'))
        
        # Immediately delete the test entry
        cursor.execute("DELETE FROM courses WHERE title = 'Test Course'")
        conn.commit()
        
        print("   ✅ Course insertion structure is correct")
    except Exception as e:
        print(f"   ❌ Course insertion test failed: {e}")
    
    conn.close()
    
    print(f"\n🎉 Fix Verification Complete!")
    print(f"💡 You can now:")
    print(f"   1. Test 'Add LinkedIn Course' in admin panel")
    print(f"   2. See correct global learnings count on admin dashboard")
    print(f"   3. Add new learning entries as admin (they'll be global)")

if __name__ == "__main__":
    fix_existing_admin_entries()
    verify_fix()
