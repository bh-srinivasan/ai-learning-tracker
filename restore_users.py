#!/usr/bin/env python3
"""
Emergency User Restoration Script
Restores users that were improperly deleted
"""

import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def restore_deleted_users():
    """Restore users that were improperly deleted"""
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Check current users
    cursor.execute('SELECT id, username FROM users ORDER BY id')
    current_users = cursor.fetchall()
    print("📊 Current users in database:")
    for user in current_users:
        print(f"   - ID: {user[0]}, Username: {user[1]}")
    
    # Check if bharath and demo1 exist
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('bharath',))
    bharath_exists = cursor.fetchone()[0] > 0
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('demo1',))
    demo1_exists = cursor.fetchone()[0] > 0
    
    restored_count = 0
    
    # Restore bharath if missing
    if not bharath_exists:
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, level, created_at, points, status, level_points) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'bharath', 
                generate_password_hash('bharath_password'),
                'Beginner',
                datetime.now(),
                0,
                'active',
                0
            ))
            print("✅ Restored user: bharath")
            restored_count += 1
        except Exception as e:
            print(f"❌ Error restoring bharath: {e}")
    else:
        print("ℹ️  User bharath already exists")
    
    # Restore demo1 if missing
    if not demo1_exists:
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, level, created_at, points, status, level_points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'demo1',
                generate_password_hash('demo1_password'),
                'Beginner', 
                datetime.now(),
                0,
                'active',
                0
            ))
            print("✅ Restored user: demo1")
            restored_count += 1
        except Exception as e:
            print(f"❌ Error restoring demo1: {e}")
    else:
        print("ℹ️  User demo1 already exists")
    
    conn.commit()
    
    # Verify final state
    cursor.execute('SELECT id, username FROM users ORDER BY id')
    final_users = cursor.fetchall()
    print(f"\n📊 Final database state ({len(final_users)} users):")
    for user in final_users:
        print(f"   - ID: {user[0]}, Username: {user[1]}")
    
    conn.close()
    
    print(f"\n🎉 Restoration complete! Restored {restored_count} users.")
    return restored_count

if __name__ == "__main__":
    print("🔄 Emergency User Restoration")
    print("=" * 40)
    restore_deleted_users()
