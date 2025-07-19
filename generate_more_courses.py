#!/usr/bin/env python3
"""Generate more courses for testing pagination"""

import sqlite3
import sys
from dynamic_course_fetcher import get_dynamic_ai_courses

def main():
    print("Generating courses...")
    
    # Get courses from dynamic fetcher
    courses = get_dynamic_ai_courses()
    print(f"Generated {len(courses)} courses from fetcher")
    
    # Connect to database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check current count
        current_count = cursor.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        print(f"Current courses in database: {current_count}")
        
        # Add courses to database
        added = 0
        for course in courses[:100]:  # Limit to 100 courses
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO courses 
                    (title, description, source, level, url, points, link, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (
                    course.get('title', 'No Title'),
                    course.get('description', 'No Description'), 
                    course.get('source', 'Dynamic'),
                    course.get('level', 'Beginner'),
                    course.get('url', course.get('link', '')),
                    course.get('points', 10),
                    course.get('link', course.get('url', ''))
                ))
                if cursor.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f"Error adding course: {e}")
                continue
        
        # Commit changes
        conn.commit()
        
        # Check final count
        final_count = cursor.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        print(f"Added {added} new courses")
        print(f"Total courses now: {final_count}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
