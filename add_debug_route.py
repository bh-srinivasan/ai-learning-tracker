#!/usr/bin/env python3
"""Add a debug route to check session status"""

import sys
import os

# Read the current app.py
with open('app.py', 'r') as f:
    content = f.read()

# Add debug route before the main block
debug_route = '''
@app.route('/debug-session')
def debug_session():
    """Debug session information"""
    session_token = session.get('session_token')
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Check memory sessions
    memory_session = None
    with session_lock:
        if session_token and session_token in active_sessions:
            memory_session = active_sessions[session_token]
    
    # Check database session
    db_session = None
    if session_token:
        conn = get_db_connection()
        try:
            session_table = get_session_table()
            query = f"""
                SELECT s.*, u.username, u.level 
                FROM {session_table} s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.session_token = ?
            """
            db_session = conn.execute(query, (session_token,)).fetchone()
        except Exception as e:
            db_session = f"Error: {e}"
        finally:
            conn.close()
    
    return f"""
    <h2>Session Debug Info</h2>
    <p><strong>Session Token:</strong> {session_token[:10] if session_token else 'None'}...</p>
    <p><strong>User ID:</strong> {user_id}</p>
    <p><strong>Username:</strong> {username}</p>
    <p><strong>Memory Session:</strong> {memory_session}</p>
    <p><strong>DB Session:</strong> {dict(db_session) if db_session and hasattr(db_session, 'keys') else db_session}</p>
    <p><strong>Total Memory Sessions:</strong> {len(active_sessions)}</p>
    """

'''

# Find where to insert the debug route (before the main block)
if 'if __name__ == \'__main__\':' in content:
    parts = content.split('if __name__ == \'__main__\':')
    new_content = parts[0] + debug_route + '\nif __name__ == \'__main__\':' + parts[1]
else:
    # Append to end if no main block found
    new_content = content + debug_route

# Write back to app.py
with open('app.py', 'w') as f:
    f.write(new_content)

print("✅ Debug route added to app.py")
print("🔄 Restart Flask app to activate debug endpoint")
print("🌐 Visit http://localhost:5000/debug-session after logging in")
