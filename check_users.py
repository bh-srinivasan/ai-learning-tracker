#!/usr/bin/env python3
"""
Check current users in the database
"""
import sqlite3

def check_users():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    users = conn.execute('SELECT id, username, level, points FROM users ORDER BY id').fetchall()
    
    print("Current users in database:")
    print("-" * 50)
    for user in users:
        print(f"ID: {user['id']}, Username: {user['username']}, Level: {user['level']}, Points: {user['points']}")
    
    if not users:
        print("No users found in database.")
    
    conn.close()

if __name__ == '__main__':
    check_users()
