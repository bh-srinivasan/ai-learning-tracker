#!/usr/bin/env python3
"""
Azure App Service Startup Script
This script ensures the database is properly initialized for Azure deployment.
"""

import os
import sqlite3
import sys
from werkzeug.security import generate_password_hash

def initialize_database():
    """Initialize the database with required tables and admin user"""
    
    # Database path for Azure
    db_path = 'ai_learning.db'
    
    print(f"🔄 Initializing database at: {db_path}")
    
    try:
        # Create database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create learnings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                date_learned DATE NOT NULL,
                category TEXT,
                level TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT,
                provider TEXT,
                level TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admin user if not exists
        admin_password = os.getenv('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        admin_hash = generate_password_hash(admin_password)
        
        cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                ('admin', admin_hash)
            )
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
        
        # Create demo user if not exists
        demo_password = os.getenv('DEMO_PASSWORD', 'DemoUserPassword123!')
        demo_hash = generate_password_hash(demo_password)
        
        cursor.execute('SELECT id FROM users WHERE username = ?', ('demo',))
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                ('demo', demo_hash)
            )
            print("✅ Demo user created")
        else:
            print("✅ Demo user already exists")
        
        conn.commit()
        conn.close()
        
        print("✅ Database initialization completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == '__main__':
    # Initialize database first
    print("🔄 Initializing database for Azure...")
    initialize_database()
    
    # Now start the main application
    print("🚀 Starting main Flask application...")
    
    # Import the main app
    import app
    
    # Get the configured Flask app instance
    flask_app = app.app
    
    # Run the app using the exact same configuration as the main app
    port = int(os.environ.get('PORT', 8000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)
