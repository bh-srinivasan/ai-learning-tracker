#!/usr/bin/env python3
"""
Check bharath user password history and potential reset triggers
"""
import sqlite3
import os

def check_bharath_user():
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check bharath user details
        print("=== BHARATH USER DETAILS ===")
        user = conn.execute("SELECT * FROM users WHERE username = 'bharath'").fetchone()
        if user:
            print(f"ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Password Hash: {user['password_hash']}")
            print(f"Created: {user['created_at']}")
            print(f"Last Login: {user['last_login']}")
            print(f"Last Activity: {user['last_activity']}")
            print(f"Login Count: {user['login_count']}")
            print(f"Status: {user['status']}")
            print()
        else:
            print("Bharath user not found!")
            return
        
        # Check security events related to bharath
        print("=== SECURITY EVENTS FOR BHARATH ===")
        events = conn.execute("""
            SELECT event_type, details, ip_address, timestamp 
            FROM security_events 
            WHERE user_id = ? OR details LIKE '%bharath%' 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (user['id'],)).fetchall()
        
        if events:
            for event in events:
                print(f"Time: {event['timestamp']}")
                print(f"Type: {event['event_type']}")
                print(f"Details: {event['details']}")
                print(f"IP: {event['ip_address']}")
                print("-" * 50)
        else:
            print("No security events found for bharath")
        
        # Check admin password reset events
        print("\n=== ADMIN PASSWORD RESET EVENTS ===")
        admin_events = conn.execute("""
            SELECT event_type, details, ip_address, timestamp 
            FROM security_events 
            WHERE event_type LIKE '%password%' OR details LIKE '%password%'
            ORDER BY timestamp DESC 
            LIMIT 5
        """).fetchall()
        
        if admin_events:
            for event in admin_events:
                print(f"Time: {event['timestamp']}")
                print(f"Type: {event['event_type']}")
                print(f"Details: {event['details']}")
                print(f"IP: {event['ip_address']}")
                print("-" * 50)
        else:
            print("No password reset events found")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking bharath user: {e}")

if __name__ == "__main__":
    check_bharath_user()
