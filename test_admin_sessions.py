import sqlite3
import logging

# Set up logging like the app does
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def test_admin_sessions_data():
    """Test the exact queries used in the admin_sessions route"""
    conn = get_db_connection()
    try:
        print("=== Testing admin_sessions route queries ===")
        
        # Get active sessions with user details
        active_sessions = conn.execute('''
            SELECT us.*, u.username, u.level, u.status,
                   datetime(us.created_at) as created_at_formatted,
                   datetime(us.expires_at) as expires_at_formatted
            FROM user_sessions us 
            JOIN users u ON us.user_id = u.id 
            WHERE us.is_active = 1 
            ORDER BY us.created_at DESC
        ''').fetchall()
        print(f"Active sessions: {len(active_sessions)}")
        
        # Get activity statistics (last 7 days) with error handling
        try:
            activity_stats = conn.execute('''
                SELECT activity_type, COUNT(*) as count
                FROM session_activity 
                WHERE datetime(timestamp) >= datetime('now', '-7 days')
                GROUP BY activity_type
                ORDER BY count DESC
            ''').fetchall()
            print(f"Activity stats: {len(activity_stats)}")
            for stat in activity_stats:
                print(f"  - {stat['activity_type']}: {stat['count']}")
        except Exception as e:
            logger.warning(f"Error fetching activity stats: {e}")
            activity_stats = []
        
        # Get login statistics (last 7 days) with error handling
        try:
            login_stats = conn.execute('''
                SELECT DATE(created_at) as login_date, COUNT(*) as login_count
                FROM user_sessions 
                WHERE datetime(created_at) >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY login_date DESC
            ''').fetchall()
            print(f"Login stats: {len(login_stats)}")
            for stat in login_stats:
                print(f"  - {stat['login_date']}: {stat['login_count']}")
        except Exception as e:
            logger.warning(f"Error fetching login stats: {e}")
            login_stats = []
        
        # Get today's login count specifically with error handling
        try:
            today_logins = conn.execute('''
                SELECT COUNT(*) as count
                FROM user_sessions 
                WHERE DATE(created_at) = DATE('now')
            ''').fetchone()
            today_login_count = today_logins['count'] if today_logins else 0
            print(f"Today's login count: {today_login_count}")
        except Exception as e:
            logger.warning(f"Error fetching today's login count: {e}")
            today_login_count = 0
        
        print(f"\nData that would be passed to template:")
        print(f"- active_sessions: {len(active_sessions)} records")
        print(f"- activity_stats: {len(activity_stats)} records")
        print(f"- login_stats: {len(login_stats)} records")
        print(f"- today_login_count: {today_login_count}")
        
        print(f"\nActivity stats details:")
        for stat in activity_stats:
            print(f"  activity_type: '{stat['activity_type']}', count: {stat['count']}")
            
        print(f"\nLogin stats details:")
        for stat in login_stats:
            print(f"  login_date: '{stat['login_date']}', login_count: {stat['login_count']}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    test_admin_sessions_data()
