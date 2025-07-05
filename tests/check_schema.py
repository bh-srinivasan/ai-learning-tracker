import sqlite3

conn = sqlite3.connect('ai_learning.db')

print("Learning entries table structure:")
for row in conn.execute('PRAGMA table_info(learning_entries)').fetchall():
    print(f"Column {row[0]}: {row[1]} ({row[2]})")

print("\nSample learning entry:")
sample = conn.execute('SELECT * FROM learning_entries LIMIT 1').fetchone()
if sample:
    print(sample)
else:
    print("No learning entries found")

conn.close()
