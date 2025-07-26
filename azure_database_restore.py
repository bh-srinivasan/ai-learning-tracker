"""
🚨 AZURE DATABASE RESTORATION - IMMEDIATE FIX
==============================================
LOCAL: 13 users, 67 courses ✅
AZURE: 0 users, 0 courses ❌ CRITICAL ISSUE

This script creates the SQL commands to restore Azure database
"""

import sqlite3
import json
from datetime import datetime

def create_azure_restore_sql():
    """Create SQL restoration script for Azure"""
    
    print("🚨 AZURE DATABASE RESTORATION")
    print("=" * 40)
    
    # Connect to local database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Extract data
    users = conn.execute('SELECT * FROM users').fetchall()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    learnings = conn.execute('SELECT * FROM learnings').fetchall()
    
    print(f"📊 LOCAL DATA TO RESTORE:")
    print(f"   👥 Users: {len(users)}")
    print(f"   📚 Courses: {len(courses)}")
    print(f"   📝 Learnings: {len(learnings)}")
    
    # Create restoration SQL
    sql_commands = []
    
    # Clear existing data first
    sql_commands.append("-- CLEAR EXISTING DATA")
    sql_commands.append("DELETE FROM learnings;")
    sql_commands.append("DELETE FROM courses;")
    sql_commands.append("DELETE FROM users;")
    sql_commands.append("")
    
    # Restore users
    sql_commands.append("-- RESTORE USERS")
    for user in users:
        username = user['username'].replace("'", "''")  # Escape quotes
        password_hash = user['password_hash'].replace("'", "''") if user['password_hash'] else ''
        created_at = user['created_at'] or 'CURRENT_TIMESTAMP'
        session_token = user['session_token'].replace("'", "''") if user['session_token'] else 'NULL'
        last_activity = f"'{user['last_activity']}'" if user['last_activity'] else 'NULL'
        last_login = f"'{user['last_login']}'" if user['last_login'] else 'NULL'
        
        sql_commands.append(f"INSERT INTO users (username, password_hash, created_at, session_token, last_activity, last_login) VALUES ('{username}', '{password_hash}', '{created_at}', {session_token if session_token == 'NULL' else f"'{session_token}'"}, {last_activity}, {last_login});")
    
    sql_commands.append("")
    
    # Restore courses
    sql_commands.append("-- RESTORE COURSES")
    for course in courses:
        title = course['title'].replace("'", "''") if course['title'] else ''
        url = course['url'].replace("'", "''") if course['url'] else ''
        source = course['source'].replace("'", "''") if course['source'] else ''
        level = course['level'].replace("'", "''") if course['level'] else ''
        description = course['description'].replace("'", "''") if course['description'] else ''
        category = course['category'].replace("'", "''") if course['category'] else ''
        difficulty = course['difficulty'].replace("'", "''") if course['difficulty'] else ''
        points = course['points'] or 0
        url_status = course['url_status'].replace("'", "''") if course['url_status'] else 'Unchecked'
        last_url_check = f"'{course['last_url_check']}'" if course['last_url_check'] else 'NULL'
        provider = course['provider'].replace("'", "''") if course['provider'] else ''
        created_at = course['created_at'] or 'CURRENT_TIMESTAMP'
        
        sql_commands.append(f"INSERT INTO courses (title, url, source, level, description, category, difficulty, points, url_status, last_url_check, provider, created_at) VALUES ('{title}', '{url}', '{source}', '{level}', '{description}', '{category}', '{difficulty}', {points}, '{url_status}', {last_url_check}, '{provider}', '{created_at}');")
    
    sql_commands.append("")
    
    # Restore learnings
    sql_commands.append("-- RESTORE LEARNINGS")
    for learning in learnings:
        user_id = learning['user_id']
        title = learning['title'].replace("'", "''") if learning['title'] else ''
        description = learning['description'].replace("'", "''") if learning['description'] else ''
        created_at = learning['created_at'] or 'CURRENT_TIMESTAMP'
        course_id = learning['course_id'] or 'NULL'
        completed = 1 if learning['completed'] else 0
        completion_date = f"'{learning['completion_date']}'" if learning['completion_date'] else 'NULL'
        
        sql_commands.append(f"INSERT INTO learnings (user_id, title, description, created_at, course_id, completed, completion_date) VALUES ({user_id}, '{title}', '{description}', '{created_at}', {course_id}, {completed}, {completion_date});")
    
    conn.close()
    
    # Save SQL file
    sql_content = '\n'.join(sql_commands)
    sql_file = f"azure_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"✅ SQL restoration file created: {sql_file}")
    
    return sql_file, len(users), len(courses), len(learnings)

def create_azure_restoration_app_code():
    """Create Flask endpoint code for Azure restoration"""
    
    app_code = '''
# ADD THIS TO YOUR AZURE app.py FILE

@app.route('/restore_database', methods=['POST'])
def restore_database():
    """EMERGENCY: Restore Azure database from SQL commands"""
    
    try:
        # Get SQL commands from request
        data = request.get_json()
        sql_commands = data.get('sql_commands', [])
        
        if not sql_commands:
            return jsonify({'error': 'No SQL commands provided'}), 400
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute each SQL command
        executed = 0
        for sql in sql_commands:
            if sql.strip() and not sql.strip().startswith('--'):
                cursor.execute(sql)
                executed += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'executed_commands': executed,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_database_status')
def check_database_status():
    """Check current database status"""
    
    try:
        conn = get_db_connection()
        
        users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        courses = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
        learnings = conn.execute('SELECT COUNT(*) FROM learnings').fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'counts': {
                'users': users,
                'courses': courses,
                'learnings': learnings
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
    
    with open('azure_restore_endpoints.py', 'w') as f:
        f.write(app_code)
    
    print("✅ Azure endpoint code created: azure_restore_endpoints.py")

def main():
    """Main restoration process"""
    
    print("🚨 AZURE DATABASE EMERGENCY RESTORATION")
    print("=" * 50)
    
    # Create SQL restoration file
    sql_file, users_count, courses_count, learnings_count = create_azure_restore_sql()
    
    # Create endpoint code
    create_azure_restoration_app_code()
    
    print("\n🎯 AZURE RESTORATION STEPS:")
    print("=" * 30)
    print("1. Copy azure_restore_endpoints.py code to your Azure app.py")
    print("2. Deploy updated app to Azure")
    print("3. Check current Azure database status:")
    print("   GET https://ai-learning-tracker.azurewebsites.net/check_database_status")
    print("4. Execute restoration:")
    print(f"   POST https://ai-learning-tracker.azurewebsites.net/restore_database")
    print(f"   Body: JSON with sql_commands from {sql_file}")
    print("5. Verify restoration completed successfully")
    
    print(f"\n📊 DATA TO RESTORE:")
    print(f"   👥 Users: {users_count}")
    print(f"   📚 Courses: {courses_count}")
    print(f"   📝 Learnings: {learnings_count}")
    
    print(f"\n💾 FILES CREATED:")
    print(f"   📄 {sql_file} - SQL restoration commands")
    print(f"   📄 azure_restore_endpoints.py - Flask endpoint code")
    
    print("\n⚠️  CRITICAL: Your Azure database will be restored!")

if __name__ == "__main__":
    main()
