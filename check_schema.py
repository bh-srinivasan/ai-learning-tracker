import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

# Check table schema
cursor.execute("PRAGMA table_info(courses)")
columns = cursor.fetchall()
print('Courses table schema:')
for column in columns:
    print(f'  {column[1]} ({column[2]}) - nullable: {not column[3]}, default: {column[4]}')

conn.close()
