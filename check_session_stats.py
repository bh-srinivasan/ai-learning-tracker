import sqlite3

def check_session_data():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    print('=== Tables in database ===')
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for table in tables:
        print(f'- {table["name"]}')
    
    print('\n=== session_activity table data ===')
    try:
        activity_stats = conn.execute('''
            SELECT activity_type, COUNT(*) as count
            FROM session_activity 
            WHERE datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY activity_type
            ORDER BY count DESC
        ''').fetchall()
        print(f'Activity stats count: {len(activity_stats)}')
        for stat in activity_stats:
            print(f'- {stat["activity_type"]}: {stat["count"]}')
    except Exception as e:
        print(f'Error with session_activity: {e}')
    
    print('\n=== user_sessions table data ===')
    try:
        login_stats = conn.execute('''
            SELECT DATE(created_at) as login_date, COUNT(*) as login_count
            FROM user_sessions 
            WHERE datetime(created_at) >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY login_date DESC
        ''').fetchall()
        print(f'Login stats count: {len(login_stats)}')
        for stat in login_stats:
            print(f'- {stat["login_date"]}: {stat["login_count"]}')
    except Exception as e:
        print(f'Error with user_sessions: {e}')
    
    print('\n=== Sample session_activity records ===')
    try:
        samples = conn.execute('''
            SELECT * FROM session_activity 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''').fetchall()
        for sample in samples:
            print(f'- {sample["timestamp"]}: {sample["activity_type"]}')
    except Exception as e:
        print(f'Error getting samples: {e}')
    
    conn.close()

if __name__ == '__main__':
    check_session_data()
