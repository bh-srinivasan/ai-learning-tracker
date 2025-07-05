#!/usr/bin/env python3
"""
Password Reset Monitor for Bharath User
This script will help detect when and how bharath's password gets reset
"""
import sqlite3
import os
import time
import hashlib
from datetime import datetime
from werkzeug.security import check_password_hash

def log_event(message):
    """Log events with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_password_hash_signature(password_hash):
    """Get a signature of the password hash for comparison"""
    return hashlib.md5(password_hash.encode()).hexdigest()[:8]

def monitor_bharath_password():
    """Monitor bharath's password for changes"""
    db_path = 'ai_learning.db'
    
    if not os.path.exists(db_path):
        log_event("❌ Database file not found!")
        return
    
    log_event("🔍 Starting password monitoring for bharath user...")
    
    # Environment variables that might affect password
    azure_demo_password = "DemoUserPassword123!"  # Current Azure setting
    script_demo_password = "DemoPass2024!"        # From setup script
    
    # Store the last known password hash signature
    last_hash_signature = None
    last_check_time = None
    
    try:
        while True:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            # Get current bharath user data
            user = conn.execute("""
                SELECT password_hash, last_login, last_activity 
                FROM users WHERE username = 'bharath'
            """).fetchone()
            
            if user:
                current_hash = user['password_hash']
                current_signature = get_password_hash_signature(current_hash)
                
                # Check if password hash changed
                if last_hash_signature and last_hash_signature != current_signature:
                    log_event("🚨 PASSWORD HASH CHANGED DETECTED!")
                    log_event(f"   Previous signature: {last_hash_signature}")
                    log_event(f"   Current signature:  {current_signature}")
                    
                    # Check what the new password might be
                    if check_password_hash(current_hash, azure_demo_password):
                        log_event("   ⚠️  NEW PASSWORD = Azure DEMO_PASSWORD (DemoUserPassword123!)")
                        log_event("   → This indicates automatic reset from Azure environment variable!")
                    elif check_password_hash(current_hash, script_demo_password):
                        log_event("   ⚠️  NEW PASSWORD = Script DEMO_PASSWORD (DemoPass2024!)")
                        log_event("   → This indicates reset from setup script!")
                    else:
                        log_event("   ✅ NEW PASSWORD = Custom password (manual change)")
                        log_event("   → This indicates manual password change by admin")
                    
                    # Check recent security events
                    recent_events = conn.execute("""
                        SELECT timestamp, event_type, details 
                        FROM security_events 
                        WHERE (user_id = 2 OR details LIKE '%bharath%') 
                        AND timestamp > datetime('now', '-10 minutes')
                        ORDER BY timestamp DESC
                    """).fetchall()
                    
                    if recent_events:
                        log_event("   📋 Recent security events (last 10 minutes):")
                        for event in recent_events:
                            log_event(f"      {event['timestamp']} - {event['event_type']}")
                            log_event(f"        {event['details']}")
                
                elif not last_hash_signature:
                    # First run
                    log_event(f"📊 Initial password hash signature: {current_signature}")
                    
                    # Check current password status
                    if check_password_hash(current_hash, azure_demo_password):
                        log_event("   ⚠️  Current password = Azure DEMO_PASSWORD")
                        log_event("   → Bharath's password is currently set to environment variable!")
                    elif check_password_hash(current_hash, script_demo_password):
                        log_event("   ⚠️  Current password = Script DEMO_PASSWORD")
                    else:
                        log_event("   ✅ Current password = Custom password")
                        log_event("   → Bharath's password is currently custom (not environment variable)")
                
                last_hash_signature = current_signature
                last_check_time = datetime.now()
                
            else:
                log_event("❌ Bharath user not found in database!")
            
            conn.close()
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
    except KeyboardInterrupt:
        log_event("🛑 Monitoring stopped by user")
    except Exception as e:
        log_event(f"❌ Error during monitoring: {e}")

def create_password_persistence_fix():
    """Create a fix to prevent automatic password resets"""
    log_event("🔧 Creating password persistence fix...")
    
    fix_script = '''#!/usr/bin/env python3
"""
Password Persistence Fix for Bharath User
This script ensures bharath's password persists across server restarts
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

def ensure_bharath_password_persistence():
    """Ensure bharath's password is not automatically reset"""
    
    # Define the target password for bharath (change this to desired password)
    BHARATH_TARGET_PASSWORD = "bharath"  # Set to your desired password
    
    db_path = 'ai_learning.db'
    if not os.path.exists(db_path):
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if bharath user exists
        user = conn.execute("SELECT id, password_hash FROM users WHERE username = 'bharath'").fetchone()
        
        if user:
            user_id, current_hash = user
            
            # Check if password has been reset to environment variable
            azure_demo_password = os.environ.get('DEMO_PASSWORD', '')
            
            if azure_demo_password and check_password_hash(current_hash, azure_demo_password):
                # Password was reset to environment variable - restore it
                print("Restoring bharath's password from environment variable reset...")
                
                new_hash = generate_password_hash(BHARATH_TARGET_PASSWORD)
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE username = 'bharath'", 
                    (new_hash,)
                )
                conn.commit()
                
                # Log the restoration
                conn.execute("""
                    INSERT INTO security_events (event_type, details, user_id, timestamp)
                    VALUES (?, ?, ?, datetime('now'))
                """, (
                    'password_persistence_fix',
                    'Restored bharath password from automatic environment reset',
                    user_id
                ))
                conn.commit()
                
                print("✅ Bharath's password restored successfully!")
            else:
                print("✅ Bharath's password is already custom (not environment variable)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error in password persistence fix: {e}")

if __name__ == "__main__":
    ensure_bharath_password_persistence()
'''
    
    with open('password_persistence_fix.py', 'w') as f:
        f.write(fix_script)
    
    log_event("✅ Created password_persistence_fix.py")
    log_event("💡 To use this fix:")
    log_event("   1. Edit the BHARATH_TARGET_PASSWORD in the script")
    log_event("   2. Run it after server restarts to restore custom password")
    log_event("   3. Add it to startup sequence if needed")

if __name__ == "__main__":
    print("🔍 Bharath Password Reset Monitor")
    print("=" * 50)
    print("This script will monitor bharath's password for automatic resets.")
    print("Press Ctrl+C to stop monitoring.")
    print()
    
    choice = input("Choose option:\n1. Start monitoring\n2. Create persistence fix script\n3. Both\nChoice (1-3): ")
    
    if choice in ['1', '3']:
        monitor_bharath_password()
    
    if choice in ['2', '3']:
        create_password_persistence_fix()
