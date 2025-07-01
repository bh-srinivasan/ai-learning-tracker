#!/usr/bin/env python3
"""
Deep investigation into Azure server password reset triggers
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta

def investigate_reset_triggers():
    """Investigate what might be triggering password resets"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        print("🔍 DEEP INVESTIGATION: Azure Password Reset Triggers")
        print("=" * 60)
        
        # 1. Check if there are any scheduled or automated events
        print("1. CHECKING FOR AUTOMATED RESET PATTERNS")
        print("-" * 40)
        
        # Get all password reset events for bharath
        reset_events = conn.execute("""
            SELECT timestamp, details, ip_address, event_type
            FROM security_events 
            WHERE (user_id = 2 OR details LIKE '%bharath%') 
            AND (event_type LIKE '%password%' OR details LIKE '%password%')
            ORDER BY timestamp ASC
        """).fetchall()
        
        if reset_events:
            print(f"Found {len(reset_events)} password-related events for bharath:")
            for i, event in enumerate(reset_events):
                print(f"  {i+1}. {event['timestamp']} - {event['event_type']}")
                print(f"     IP: {event['ip_address']} | Details: {event['details']}")
                
                # Check time patterns
                if i > 0:
                    prev_time = datetime.fromisoformat(reset_events[i-1]['timestamp'].replace('Z', '+00:00'))
                    curr_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    time_diff = curr_time - prev_time
                    print(f"     Time since last: {time_diff}")
                print()
        
        # 2. Check for bulk password reset events
        print("2. CHECKING BULK PASSWORD RESET EVENTS")
        print("-" * 40)
        
        bulk_resets = conn.execute("""
            SELECT timestamp, details, ip_address
            FROM security_events 
            WHERE event_type = 'admin_password_reset' 
            AND details LIKE '%users%'
            ORDER BY timestamp DESC
        """).fetchall()
        
        if bulk_resets:
            print(f"Found {len(bulk_resets)} bulk password reset events:")
            for event in bulk_resets:
                print(f"  {event['timestamp']} - {event['details']}")
                print(f"  IP: {event['ip_address']}")
                print()
        else:
            print("  No bulk password reset events found")
        
        # 3. Check session patterns that might indicate automated access
        print("3. CHECKING SESSION PATTERNS")
        print("-" * 40)
        
        admin_sessions = conn.execute("""
            SELECT created_at, ip_address, user_agent, expires_at
            FROM user_sessions 
            WHERE user_id = 1
            ORDER BY created_at DESC
            LIMIT 10
        """).fetchall()
        
        if admin_sessions:
            print("Recent admin sessions:")
            for session in admin_sessions:
                print(f"  {session['created_at']} from {session['ip_address']}")
                print(f"    User Agent: {session['user_agent']}")
                print(f"    Expires: {session['expires_at']}")
                print()
        
        # 4. Check if there are any deployment-triggered events
        print("4. CHECKING FOR DEPLOYMENT-RELATED EVENTS")
        print("-" * 40)
        
        # Look for events that happen close to each other (might indicate automation)
        recent_events = conn.execute("""
            SELECT timestamp, event_type, details, ip_address
            FROM security_events 
            WHERE timestamp > datetime('now', '-7 days')
            ORDER BY timestamp DESC
        """).fetchall()
        
        # Group events by time proximity (within 5 minutes)
        if recent_events:
            print("Recent security events (last 7 days):")
            current_group = []
            last_time = None
            
            for event in recent_events:
                event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                
                if last_time and (last_time - event_time) < timedelta(minutes=5):
                    current_group.append(event)
                else:
                    if current_group:
                        print(f"\n  Event Group (within 5 minutes):")
                        for group_event in current_group:
                            print(f"    {group_event['timestamp']} - {group_event['event_type']}")
                            print(f"      {group_event['details']}")
                    current_group = [event]
                    last_time = event_time
            
            # Print the last group
            if current_group:
                print(f"\n  Event Group (within 5 minutes):")
                for group_event in current_group:
                    print(f"    {group_event['timestamp']} - {group_event['event_type']}")
                    print(f"      {group_event['details']}")
        
        # 5. Check current bharath password status
        print("\n5. CURRENT BHARATH PASSWORD STATUS")
        print("-" * 40)
        
        bharath_user = conn.execute("""
            SELECT password_hash, last_login, last_activity, created_at
            FROM users WHERE username = 'bharath'
        """).fetchone()
        
        if bharath_user:
            # Test if current password matches environment variable
            from werkzeug.security import check_password_hash
            demo_password = "DemoUserPassword123!"  # Azure DEMO_PASSWORD
            
            if check_password_hash(bharath_user['password_hash'], demo_password):
                print("  ⚠️  PASSWORD IS SET TO AZURE DEMO_PASSWORD")
                print("      This indicates recent automatic reset!")
            else:
                print("  ✅ Password is NOT set to Azure DEMO_PASSWORD")
                print("      Password appears to be custom/manual")
            
            print(f"  Last Login: {bharath_user['last_login']}")
            print(f"  Last Activity: {bharath_user['last_activity']}")
            print(f"  Account Created: {bharath_user['created_at']}")
        
        conn.close()
        
        # 6. Check Azure-specific automation files
        print("\n6. CHECKING FOR AZURE AUTOMATION FILES")
        print("-" * 40)
        
        automation_files = [
            'web.config',
            'startup.py', 
            '.deployment',
            'deploy.cmd',
            'requirements.txt',
            'runtime.txt'
        ]
        
        for filename in automation_files:
            if os.path.exists(filename):
                print(f"  ✅ Found: {filename}")
                if filename == 'startup.py':
                    print("     → This runs on Azure startup - checking for password reset calls")
            else:
                print(f"  ❌ Not found: {filename}")
        
        print("\n" + "=" * 60)
        print("INVESTIGATION COMPLETE")
        
    except Exception as e:
        print(f"Error during investigation: {e}")

if __name__ == "__main__":
    investigate_reset_triggers()
