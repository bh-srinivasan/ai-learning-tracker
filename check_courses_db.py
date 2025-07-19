#!/usr/bin/env python3
"""Check current database courses"""

import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

# Get total count
cursor.execute('SELECT COUNT(*) FROM courses')
total = cursor.fetchone()[0]
print(f"Total courses in database: {total}")

# Get breakdown by source
cursor.execute('''
    SELECT source, COUNT(*) as count 
    FROM courses 
    WHERE source IS NOT NULL AND source != ''
    GROUP BY source 
    ORDER BY count DESC
''')

results = cursor.fetchall()
print("\nCourses by source:")
for source, count in results:
    print(f"  {source}: {count} courses")

# Get some sample titles
cursor.execute('SELECT title, source FROM courses LIMIT 10')
samples = cursor.fetchall()
print("\nSample course titles:")
for title, source in samples:
    print(f"  - {title} ({source or 'Unknown'})")

conn.close()
