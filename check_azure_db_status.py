"""
Standalone script to check Azure database status
"""
import os
import sqlite3
import requests
from datetime import datetime

def check_azure_db_status():
    """Check Azure app database status"""
    azure_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    # Check if /db-status endpoint exists (if we added it)
    try:
        response = requests.get(f"{azure_url}/db-status", timeout=30)
        print(f"Azure DB Status Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Database Status:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Could not check Azure DB status: {e}")
    
    # Test local database for comparison
    print("\n" + "="*50)
    print("LOCAL DATABASE STATUS:")
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        # Check if users table exists
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchall()
        users_table_exists = len(tables) > 0
        print(f"Users table exists: {users_table_exists}")
        
        if users_table_exists:
            # Check if admin user exists
            admin_user = conn.execute('SELECT username, created_at FROM users WHERE username = ?', ('admin',)).fetchone()
            admin_exists = admin_user is not None
            print(f"Admin user exists: {admin_exists}")
            if admin_user:
                print(f"Admin created at: {admin_user['created_at']}")
            
            # Get total user count
            user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
            print(f"Total users: {user_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Local database error: {e}")

if __name__ == '__main__':
    check_azure_db_status()
