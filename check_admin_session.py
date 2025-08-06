#!/usr/bin/env python3
"""Debug admin session management in Flask app"""

import sqlite3
import os

def check_admin_session():
    print("🔍 Checking admin session state...")
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find admin user
    cursor.execute("SELECT id, username, level FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        print(f"✅ Admin user found: ID={admin_user['id']}, Level={admin_user['level']}")
        
        # Check recent sessions for admin
        cursor.execute("""
            SELECT session_token, user_id, created_at, is_active 
            FROM user_sessions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (admin_user['id'],))
        
        sessions = cursor.fetchall()
        print(f"✅ Admin has {len(sessions)} recent sessions")
        
        for session in sessions:
            print(f"   - Token: {session['session_token'][:10]}... Created: {session['created_at']} Active: {session['is_active']}")
    else:
        print("❌ Admin user not found!")
    
    conn.close()

def check_session_cleanup():
    print("\n🧹 Checking for old sessions...")
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Count total sessions
    cursor.execute("SELECT COUNT(*) as count FROM user_sessions")
    total = cursor.fetchone()[0]
    print(f"📊 Total sessions in database: {total}")
    
    # Check sessions from today
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM user_sessions 
        WHERE date(created_at) = date('now')
    """)
    today = cursor.fetchone()[0]
    print(f"📊 Sessions created today: {today}")
    
    conn.close()

if __name__ == "__main__":
    check_admin_session()
    check_session_cleanup()
