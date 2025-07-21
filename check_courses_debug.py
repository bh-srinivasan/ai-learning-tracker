#!/usr/bin/env python3

import sqlite3

try:
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Check if courses table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
    table_exists = cursor.fetchone()
    print(f'Courses table exists: {table_exists is not None}')
    
    if table_exists:
        # Check table structure
        cursor.execute('PRAGMA table_info(courses)')
        columns = cursor.fetchall()
        print('Table columns:')
        for col in columns:
            print(f'  - {col[1]} ({col[2]})')
        
        # Count total courses
        cursor.execute('SELECT COUNT(*) FROM courses')
        total = cursor.fetchone()[0]
        print(f'Total courses: {total}')
        
        if total > 0:
            # Get sample data
            cursor.execute('SELECT id, title, points, level FROM courses LIMIT 5')
            samples = cursor.fetchall()
            print('Sample courses:')
            for sample in samples:
                print(f'  ID: {sample[0]}, Title: {sample[1][:40]}..., Points: {sample[2]}, Level: {sample[3]}')
            
            # Check distribution by new point ranges
            print('\nPoints distribution:')
            ranges = {
                '0-100': (0, 100),
                '100-200': (100, 200),
                '200-300': (200, 300),
                '300-400': (300, 400),
                '400+': (400, 9999)
            }
            
            for range_name, (min_points, max_points) in ranges.items():
                if max_points == 9999:
                    cursor.execute('SELECT COUNT(*) FROM courses WHERE points >= ?', (min_points,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM courses WHERE points >= ? AND points < ?', (min_points, max_points))
                count = cursor.fetchone()[0]
                print(f'  {range_name}: {count} courses')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
