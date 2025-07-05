import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

print("All tables:", tables)

missing_tables = []
required_tables = ['level_points', 'course_search_configs', 'level_settings']

for table in required_tables:
    if table not in tables:
        missing_tables.append(table)
        print(f"MISSING: {table}")
    else:
        print(f"EXISTS: {table}")

print("Missing tables:", missing_tables)
conn.close()
