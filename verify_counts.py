import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

# Get total course count
cursor.execute('SELECT COUNT(*) FROM courses')
total_count = cursor.fetchone()[0]
print(f'Total courses in database: {total_count}')

# Get manual entries count
cursor.execute('SELECT COUNT(*) FROM courses WHERE source = "Manual"')
manual_count = cursor.fetchone()[0]
print(f'Manual entries: {manual_count}')

# Get courses by source
cursor.execute('SELECT source, COUNT(*) FROM courses GROUP BY source ORDER BY COUNT(*) DESC')
sources = cursor.fetchall()
print('\nCourses by source:')
for source, count in sources:
    print(f'  {source}: {count}')

conn.close()
