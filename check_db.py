import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

# Check total courses
cursor.execute('SELECT COUNT(*) FROM courses')
total = cursor.fetchone()[0]
print(f'Total courses: {total}')

# Check recent courses
cursor.execute('SELECT title, source FROM courses ORDER BY created_at DESC LIMIT 10')
courses = cursor.fetchall()
print('\nRecent courses:')
for title, source in courses:
    print(f'  {title} ({source})')

# Check if any courses exist with the new titles we're trying to add
test_titles = [
    'Microsoft Copilot for Productivity',
    'AI for Product Managers', 
    'Introduction to Microsoft Copilot',
    'AI for Everyone by Andrew Ng'
]

print('\nChecking for specific course titles:')
for title in test_titles:
    cursor.execute('SELECT COUNT(*) FROM courses WHERE title = ?', (title,))
    count = cursor.fetchone()[0]
    print(f'  "{title}": {count} matches')

conn.close()
