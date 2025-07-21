#!/usr/bin/env python3
"""Check admin credentials"""

import sqlite3

conn = sqlite3.connect('ai_learning.db')
cursor = conn.cursor()

cursor.execute('SELECT username, password FROM users WHERE username = ?', ('admin',))
result = cursor.fetchone()

if result:
    print(f"Admin username: {result[0]}")
    print(f"Admin password: {result[1]}")
else:
    print("Admin user not found")

conn.close()
