#!/usr/bin/env python3
"""Check users table structure"""

import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

# Get table structure
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("Users table structure:")
for column in columns:
    print(f"  {column[1]} ({column[2]})")

# Get admin user data
cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
result = cursor.fetchone()

if result:
    print(f"\nAdmin user data: {result}")
else:
    print("\nAdmin user not found")

conn.close()
