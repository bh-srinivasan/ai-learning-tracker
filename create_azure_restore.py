"""
🚨 FORCE AZURE DATABASE RESTORATION
===================================
Upload local database directly to Azure App Service to restore all data
"""

import sqlite3
import os
import json
from datetime import datetime

def create_azure_data_restore_script():
    """Create SQL script to restore data in Azure"""
    
    if not os.path.exists('ai_learning.db'):
        print("❌ Local database not found")
        return False
    
    # Read all data from local database
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Get users data
    users = conn.execute('SELECT * FROM users').fetchall()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    learnings = conn.execute('SELECT * FROM learnings').fetchall()
    
    print(f"📊 EXTRACTING DATA:")
    print(f"   Users: {len(users)}")
    print(f"   Courses: {len(courses)}")
    print(f"   Learning entries: {len(learnings)}")
    
    # Create restoration script
    restore_script = f"""#!/usr/bin/env python3
'''
Azure Database Restoration Script
Generated: {datetime.now().isoformat()}
Purpose: Restore {len(users)} users, {len(courses)} courses, {len(learnings)} learning entries
'''

import sqlite3
import os
from werkzeug.security import generate_password_hash

def restore_azure_database():
    db_path = 'ai_learning.db'
    
    # Initialize database if needed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_token TEXT,
            last_activity TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT,
            source TEXT,
            level TEXT,
            description TEXT,
            category TEXT,
            difficulty TEXT,
            points INTEGER DEFAULT 0,
            url_status TEXT DEFAULT 'Unchecked',
            last_url_check TIMESTAMP,
            provider TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            course_id INTEGER,
            completed BOOLEAN DEFAULT FALSE,
            completion_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM learnings')
    cursor.execute('DELETE FROM courses') 
    cursor.execute('DELETE FROM users')
    
    print("🗑️ Cleared existing data")
    
    # Restore users
    users_data = {json.dumps([dict(user) for user in users], indent=2)}
    
    for user_data in users_data:
        cursor.execute('''
            INSERT INTO users (username, password_hash, created_at, session_token, last_activity, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_data.get('username'),
            user_data.get('password_hash'),
            user_data.get('created_at'),
            user_data.get('session_token'),
            user_data.get('last_activity'),
            user_data.get('last_login')
        ))
    
    print(f"✅ Restored {{len(users_data)}} users")
    
    # Restore courses  
    courses_data = {json.dumps([dict(course) for course in courses], indent=2)}
    
    for course_data in courses_data:
        cursor.execute('''
            INSERT INTO courses (title, url, source, level, description, category, difficulty, points, url_status, last_url_check, provider, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            course_data.get('title'),
            course_data.get('url'),
            course_data.get('source'),
            course_data.get('level'), 
            course_data.get('description'),
            course_data.get('category'),
            course_data.get('difficulty'),
            course_data.get('points', 0),
            course_data.get('url_status', 'Unchecked'),
            course_data.get('last_url_check'),
            course_data.get('provider'),
            course_data.get('created_at')
        ))
    
    print(f"✅ Restored {{len(courses_data)}} courses")
    
    # Restore learnings
    learnings_data = {json.dumps([dict(learning) for learning in learnings], indent=2)}
    
    for learning_data in learnings_data:
        cursor.execute('''
            INSERT INTO learnings (user_id, title, description, created_at, course_id, completed, completion_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            learning_data.get('user_id'),
            learning_data.get('title'),
            learning_data.get('description'),
            learning_data.get('created_at'),
            learning_data.get('course_id'),
            learning_data.get('completed', False),
            learning_data.get('completion_date')
        ))
    
    print(f"✅ Restored {{len(learnings_data)}} learning entries")
    
    conn.commit()
    conn.close()
    
    print("🎉 AZURE DATABASE RESTORATION COMPLETE!")
    print("✅ All data has been restored successfully")

if __name__ == "__main__":
    print("🚨 AZURE DATABASE RESTORATION")
    print("==============================")
    restore_azure_database()
"""
    
    # Write the restoration script
    with open('azure_restore_data.py', 'w', encoding='utf-8') as f:
        f.write(restore_script)
    
    conn.close()
    print("✅ Azure restoration script created: azure_restore_data.py")
    return True

def create_azure_deployment_with_data():
    """Create deployment that includes data restoration"""
    
    deployment_script = """#!/bin/bash
# Azure Deployment with Data Restoration

echo "🚀 Deploying to Azure with data restoration..."

# Deploy code first
git add azure_restore_data.py
git commit -m "Add Azure data restoration script"
git push azure master

# Wait for deployment
sleep 30

# Run data restoration via Azure CLI
echo "🔄 Running data restoration on Azure..."
az webapp ssh --resource-group ai-learning-rg --name ai-learning-tracker --command "cd /home/site/wwwroot && python azure_restore_data.py"

echo "✅ Deployment and data restoration complete!"
"""
    
    with open('deploy_with_data_restore.sh', 'w') as f:
        f.write(deployment_script)
    
    print("✅ Created deployment script: deploy_with_data_restore.sh")

if __name__ == "__main__":
    print("🚨 AZURE DATA RESTORATION GENERATOR")
    print("=====================================")
    
    success = create_azure_data_restore_script()
    if success:
        create_azure_deployment_with_data()
        print("\n🎯 NEXT STEPS:")
        print("1. Run: git add azure_restore_data.py")
        print("2. Run: git commit -m 'Add data restoration'")
        print("3. Run: git push azure master")
        print("4. Run: python azure_restore_data.py (on Azure)")
        print("\nOR run the automated script:")
        print("bash deploy_with_data_restore.sh")
