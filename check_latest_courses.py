import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

# Get the latest 10 courses
cursor.execute('SELECT title, source, url, created_at FROM courses ORDER BY created_at DESC LIMIT 10')
latest_courses = cursor.fetchall()

print('Latest 10 courses:')
for i, (title, source, url, created_at) in enumerate(latest_courses, 1):
    print(f'{i}. {title}')
    print(f'   Source: {source}')
    print(f'   URL: {url}')
    print(f'   Created: {created_at}')
    print()

conn.close()
