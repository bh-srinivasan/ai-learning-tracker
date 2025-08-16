#!/usr/bin/env python3
"""
Test the admin sessions page data collection
"""
import sqlite3

def test_admin_sessions_data():
    """Test the data that will be passed to admin sessions template"""
    
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🧪 Testing Admin Sessions Data Collection...")
    print("=" * 50)
    
    # Test 1: Active sessions
    print("1. Active Sessions:")
    active_sessions = cursor.execute('''
        SELECT 
            us.*,
            u.username,
            u.level,
            'Active' as session_status,
            datetime(us.created_at, 'localtime') as created_at_formatted,
            datetime(us.expires_at, 'localtime') as expires_at_formatted
        FROM user_sessions us 
        JOIN users u ON us.user_id = u.id 
        WHERE us.is_active = 1 
        ORDER BY us.created_at DESC
    ''').fetchall()
    
    print(f"   Count: {len(active_sessions)}")
    for i, session in enumerate(active_sessions[:3]):
        print(f"   {i+1}. {session['username']} - {session['session_status']}")
    
    # Test 2: Activity statistics
    print("\n2. Activity Statistics (Last 7 days):")
    activity_stats = cursor.execute('''
        SELECT activity_type, COUNT(*) as count
        FROM session_activity 
        WHERE datetime(timestamp) >= datetime('now', '-7 days')
        GROUP BY activity_type
        ORDER BY count DESC
    ''').fetchall()
    
    print(f"   Count: {len(activity_stats)}")
    total_activity = sum(stat['count'] for stat in activity_stats)
    print(f"   Total Activity: {total_activity}")
    for stat in activity_stats:
        print(f"   - {stat['activity_type']}: {stat['count']}")
    
    # Test 3: Login statistics
    print("\n3. Daily Login Statistics (Last 7 days):")
    login_stats = cursor.execute('''
        SELECT DATE(created_at) as login_date, COUNT(*) as login_count
        FROM user_sessions 
        WHERE datetime(created_at) >= datetime('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY login_date DESC
    ''').fetchall()
    
    print(f"   Count: {len(login_stats)}")
    for stat in login_stats:
        print(f"   - {stat['login_date']}: {stat['login_count']} logins")
    
    # Test 4: Today's login count
    print("\n4. Today's Login Count:")
    today_date = cursor.execute("SELECT DATE('now')").fetchone()[0]
    today_login_count = 0
    for stat in login_stats:
        if stat['login_date'] == today_date:
            today_login_count = stat['login_count']
            break
    
    print(f"   Today ({today_date}): {today_login_count} logins")
    
    print("\n" + "=" * 50)
    print("✅ Data collection test completed!")
    print(f"📊 Summary:")
    print(f"   - Active Sessions: {len(active_sessions)}")
    print(f"   - Activity Types: {len(activity_stats)}")
    print(f"   - Login Days: {len(login_stats)}")
    print(f"   - Today's Logins: {today_login_count}")
    print(f"   - Total Activity: {total_activity}")
    
    conn.close()
    return len(activity_stats) > 0 and len(login_stats) > 0

if __name__ == "__main__":
    test_admin_sessions_data()
