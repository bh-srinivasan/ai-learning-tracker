#!/usr/bin/env python3
"""
Quick check of current database state and Excel file validation
"""

import sqlite3
import pandas as pd

def check_current_state():
    """Check current database and Excel file state"""
    print("📊 Current Database & Excel File State")
    print("=" * 50)
    
    # Check database
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM courses')
        total_courses = cursor.fetchone()[0]
        print(f"Total courses in database: {total_courses}")
        
        cursor.execute('SELECT level, COUNT(*) FROM courses GROUP BY level')
        level_counts = cursor.fetchall()
        print("Course distribution by level:")
        for level, count in level_counts:
            print(f"  {level}: {count}")
        
        # Check for sample course URLs to see if any were already uploaded
        sample_urls = [
            'https://example.com/python-basics',
            'https://example.com/web-development', 
            'https://example.com/data-science',
            'https://example.com/machine-learning'
        ]
        
        found_samples = []
        for url in sample_urls:
            cursor.execute('SELECT title FROM courses WHERE url = ?', (url,))
            result = cursor.fetchone()
            if result:
                found_samples.append((url, result[0]))
        
        if found_samples:
            print(f"\nFound {len(found_samples)} sample courses already in database:")
            for url, title in found_samples:
                print(f"  - {title}")
            print("  (These would be skipped as duplicates)")
        else:
            print("\nNo sample courses found in database - upload should add all 4")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
    
    # Check Excel file
    try:
        df = pd.read_excel('sample_courses_upload.xlsx')
        print(f"\nExcel file contains {len(df)} courses:")
        for i, row in df.iterrows():
            print(f"  {i+1}. {row['title']} ({row['level']}, {row['points']} pts)")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
    
    print("\n" + "=" * 50)
    print("To upload successfully:")
    print("1. Make sure you're logged in as admin in the browser")
    print("2. Go to Admin -> Manage Courses")
    print("3. Click 'Upload Excel' button")
    print("4. Select 'sample_courses_upload.xlsx'")
    print("5. Click 'Upload'")

if __name__ == "__main__":
    check_current_state()
