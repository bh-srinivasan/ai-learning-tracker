import sqlite3
import os

try:
    if os.path.exists('ai_learning.db'):
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, LENGTH(password_hash) as hash_len, created_at FROM users')
        users = cursor.fetchall()
        print(f"Database Status: Found {len(users)} users")
        for username, hash_len, created in users:
            print(f"- {username}: hash_length={hash_len}, created={created}")
        conn.close()
    else:
        print("Database file not found")
except Exception as e:
    print(f"Error: {e}")
