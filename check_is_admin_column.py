#!/usr/bin/env python3
"""Check if is_admin column exists in Azure SQL users table"""

import os
import pyodbc

def check_is_admin_column():
    # Database connection
    server = 'ai-learning-sql-centralus.database.windows.net'
    database = 'ai-learning-db'
    username = 'ailearningadmin'
    password = os.environ.get('AZURE_SQL_PASSWORD')

    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    try:
        # Check users table structure
        print('=== USERS TABLE COLUMNS ===')
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users'
            ORDER BY ORDINAL_POSITION
        """)
        for col in cursor.fetchall():
            print(f'{col[0]}: {col[1]} (NULL: {col[2]})')

        # Check demo user to see is_admin value
        print('\n=== DEMO USER DATA ===')
        cursor.execute('SELECT id, username, level, points, is_admin FROM users WHERE username = ?', ('demo',))
        demo_user = cursor.fetchone()
        if demo_user:
            print(f'Demo user: ID={demo_user[0]}, username={demo_user[1]}, level={demo_user[2]}, points={demo_user[3]}, is_admin={demo_user[4]}')
        else:
            print('Demo user not found')

        # Check admin user
        print('\n=== ADMIN USER DATA ===')
        cursor.execute('SELECT id, username, level, points, is_admin FROM users WHERE username = ?', ('admin',))
        admin_user = cursor.fetchone()
        if admin_user:
            print(f'Admin user: ID={admin_user[0]}, username={admin_user[1]}, level={admin_user[2]}, points={admin_user[3]}, is_admin={admin_user[4]}')
        else:
            print('Admin user not found')

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_is_admin_column()
