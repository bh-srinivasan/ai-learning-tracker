#!/usr/bin/env python3
"""
Check session activity table and add sample data if needed
"""
import sqlite3
from datetime import datetime, timedelta

def check_and_setup_session_activity():
    """Check session activity table and add sample data if needed"""
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Check if session_activity table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='session_activity'
    """)
    table_exists = cursor.fetchone() is not None
    
    print(f"session_activity table exists: {table_exists}")
    
    if not table_exists:
        print("Creating session_activity table...")
        cursor.execute("""
            CREATE TABLE session_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
        print("✅ session_activity table created")
    
    # Check current data
    cursor.execute('SELECT COUNT(*) FROM session_activity')
    count = cursor.fetchone()[0]
    print(f"Records in session_activity: {count}")
    
    # Add sample data if empty
    if count == 0:
        print("Adding sample session activity data...")
        
        # Get some user IDs
        cursor.execute('SELECT id FROM users LIMIT 3')
        user_ids = [row[0] for row in cursor.fetchall()]
        
        if user_ids:
            # Add sample activities over the last 7 days
            sample_activities = [
                ('session_created', -1),
                ('session_created', -2),  
                ('page_access', -1),
                ('page_access', -1),
                ('page_access', -2),
                ('session_invalidated', -2),
                ('session_created', -3),
                ('page_access', -3),
                ('page_access', -4),
                ('session_expired', -5),
            ]
            
            for activity_type, days_ago in sample_activities:
                timestamp = datetime.now() + timedelta(days=days_ago)
                cursor.execute("""
                    INSERT INTO session_activity (user_id, activity_type, timestamp, ip_address)
                    VALUES (?, ?, ?, ?)
                """, (user_ids[0], activity_type, timestamp.strftime('%Y-%m-%d %H:%M:%S'), '127.0.0.1'))
            
            conn.commit()
            print(f"✅ Added {len(sample_activities)} sample activity records")
        else:
            print("⚠️ No users found to add sample data")
    
    # Show current stats
    cursor.execute("""
        SELECT activity_type, COUNT(*) as count
        FROM session_activity 
        WHERE datetime(timestamp) >= datetime('now', '-7 days')
        GROUP BY activity_type
        ORDER BY count DESC
    """)
    stats = cursor.fetchall()
    
    print("\n📊 Activity Stats (Last 7 days):")
    for activity_type, count in stats:
        print(f"  - {activity_type}: {count}")
    
    conn.close()
    return True

if __name__ == "__main__":
    check_and_setup_session_activity()
