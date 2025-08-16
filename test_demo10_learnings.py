#!/usr/bin/env python3
"""
Test the My Learning page fix for demo10 user
"""
import sqlite3

def test_demo10_learnings():
    """Test demo10 user's learning entries"""
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get demo10 user
    cursor.execute("SELECT id, username FROM users WHERE username = ?", ('demo10',))
    user = cursor.fetchone()
    
    if not user:
        print("❌ Demo10 user not found!")
        conn.close()
        return False
    
    print(f"✅ Found user: {user['username']} (ID: {user['id']})")
    
    # Get learning entries
    cursor.execute('''
        SELECT * FROM learning_entries 
        WHERE user_id = ? 
        ORDER BY date_added DESC
    ''', (user['id'],))
    
    entries = cursor.fetchall()
    
    print(f"📚 Learning entries found: {len(entries)}")
    
    if entries:
        print("📖 Entries:")
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry['title']}")
            print(f"     Description: {entry['description'][:50]}...")
            print(f"     Date: {entry['date_added']}")
            print(f"     Tags: {entry['tags']}")
            print()
    else:
        print("❌ No learning entries found for demo10!")
    
    conn.close()
    return len(entries) > 0

if __name__ == "__main__":
    success = test_demo10_learnings()
    if success:
        print("🎉 Demo10 has learning entries - the My Learning page should now show them!")
    else:
        print("❌ No learning entries found for demo10")
