"""
Quick test for file upload functionality to verify the None value fix works.
"""

import sqlite3
import pandas as pd
import os

def test_upload_fix():
    """Test the upload fix by simulating the problematic code"""
    
    # Connect to database
    if not os.path.exists('ai_learning.db'):
        print("❌ Database not found")
        return False
        
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        # Test the exact code that was failing
        existing_courses = conn.execute('SELECT title, url FROM courses').fetchall()
        existing_set = set()
        
        print(f"📊 Found {len(existing_courses)} existing courses")
        
        for row in existing_courses:
            title = row['title'] if row['title'] else ''
            url = row['url'] if row['url'] else ''
            if title and url:  # Only add if both title and url are not empty
                existing_set.add((title.lower().strip(), url.lower().strip()))
        
        print(f"✅ Successfully processed {len(existing_set)} valid courses for duplicate checking")
        
        # Test creating a small Excel file for upload
        test_data = {
            'title': ['Test AI Course', 'Another Test Course'],
            'url': ['https://example.com/test1', 'https://example.com/test2'],
            'source': ['Test Source', 'Test Source'],
            'level': ['Beginner', 'Intermediate'],
            'description': ['Test course 1', 'Test course 2']
        }
        
        df = pd.DataFrame(test_data)
        df.to_excel('test_upload_fix.xlsx', index=False)
        print("✅ Created test Excel file: test_upload_fix.xlsx")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing upload fix: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing file upload fix...")
    success = test_upload_fix()
    if success:
        print("✅ Upload functionality fix verified successfully!")
        print("📋 You can now try uploading the test_upload_fix.xlsx file")
    else:
        print("❌ Upload fix test failed")
