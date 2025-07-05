import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

print("Checking URL Status values in database:")
cursor.execute('SELECT DISTINCT url_status, COUNT(*) FROM courses GROUP BY url_status')
for row in cursor.fetchall():
    print(f'URL Status: "{row[0]}" - Count: {row[1]}')

print("\nSample courses with their URL status:")
cursor.execute('SELECT id, title, url_status FROM courses WHERE url_status IS NOT NULL LIMIT 10')
for row in cursor.fetchall():
    title = row[1][:40] if row[1] else "N/A"
    print(f'ID: {row[0]}, Title: {title}..., URL Status: "{row[2]}"')

conn.close()
