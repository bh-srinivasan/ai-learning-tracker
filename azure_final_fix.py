#!/usr/bin/env python3
"""
Final Azure Fix - Database and App Simplification
Focus on the core issue: database file access in Azure
"""

import os
import sqlite3
import shutil
from datetime import datetime

def create_minimal_working_app():
    """Create a minimal version of the app that should work in Azure"""
    print("🔧 Creating Minimal Working App...")
    
    minimal_app = '''#!/usr/bin/env python3
"""
Minimal Azure-compatible version of AI Learning Tracker
Simplified to work reliably in Azure App Service
"""

import os
import sys
import sqlite3
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-azure')

# Database functions
def get_db_connection():
    """Get database connection with error handling"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
        logger.info(f"Connecting to database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """Initialize database with basic structure"""
    try:
        conn = get_db_connection()
        
        # Create users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create learning entries table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS learning_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_title TEXT NOT NULL,
                learning_notes TEXT,
                completion_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create default admin user if not exists
        cursor = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            password_hash = generate_password_hash(admin_password)
            conn.execute(
                'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                ('admin', password_hash, True)
            )
            logger.info("Created default admin user")
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

# Routes
@app.route('/')
def index():
    """Home page"""
    try:
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return '''
        <html>
        <head><title>AI Learning Tracker</title></head>
        <body>
            <h1>AI Learning Tracker</h1>
            <p>Welcome to the AI Learning Tracker!</p>
            <p><a href="/login">Login</a> | <a href="/register">Register</a></p>
            <p><strong>Status:</strong> App is running on Azure! ✅</p>
            <p><strong>Time:</strong> {}</p>
        </body>
        </html>
        '''.format(datetime.now())
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return f"Error: {e}", 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'users': user_count,
            'time': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password')
        
        return '''
        <html>
        <head><title>Login - AI Learning Tracker</title></head>
        <body>
            <h2>Login</h2>
            <form method="post">
                <p>Username: <input type="text" name="username" required></p>
                <p>Password: <input type="password" name="password" required></p>
                <p><input type="submit" value="Login"></p>
            </form>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        '''
    except Exception as e:
        logger.error(f"Login route error: {e}")
        return f"Login error: {e}", 500

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        entries = conn.execute(
            'SELECT * FROM learning_entries WHERE user_id = ? ORDER BY created_at DESC',
            (session['user_id'],)
        ).fetchall()
        conn.close()
        
        return f'''
        <html>
        <head><title>Dashboard - AI Learning Tracker</title></head>
        <body>
            <h2>Welcome, {session['username']}!</h2>
            <p>Learning Entries: {len(entries)}</p>
            <p><a href="/logout">Logout</a></p>
            <p><strong>App Status:</strong> Running successfully on Azure ✅</p>
        </body>
        </html>
        '''
    except Exception as e:
        logger.error(f"Dashboard route error: {e}")
        return f"Dashboard error: {e}", 500

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return f'''
    <html>
    <head><title>Error - AI Learning Tracker</title></head>
    <body>
        <h2>Something went wrong</h2>
        <p>Error: {error}</p>
        <p><a href="/">Back to Home</a></p>
        <p><strong>Debug info:</strong> {datetime.now()}</p>
    </body>
    </html>
    ''', 500

# Initialize database on startup
try:
    logger.info("Initializing application...")
    init_success = init_db()
    if init_success:
        logger.info("✅ Application initialized successfully")
    else:
        logger.error("❌ Database initialization failed")
except Exception as e:
    logger.error(f"❌ Application initialization error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
'''
    
    with open('app_minimal.py', 'w') as f:
        f.write(minimal_app)
    
    print("✅ Created app_minimal.py")

def fix_database_permissions():
    """Ensure database file has correct permissions and structure"""
    print("🗄️ Fixing Database Permissions and Structure...")
    
    db_file = 'ai_learning.db'
    
    try:
        if os.path.exists(db_file):
            # Check current size and permissions
            size = os.path.getsize(db_file)
            print(f"Current database size: {size} bytes")
            
            # Try to open and verify structure
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Database tables: {[table[0] for table in tables]}")
            
            # Ensure all required tables exist
            required_tables = ['users', 'learning_entries']
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
                if not cursor.fetchone():
                    print(f"Missing table: {table}")
                    # Create missing table
                    if table == 'users':
                        cursor.execute('''
                            CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                password_hash TEXT NOT NULL,
                                is_admin BOOLEAN DEFAULT FALSE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                    elif table == 'learning_entries':
                        cursor.execute('''
                            CREATE TABLE learning_entries (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                course_title TEXT NOT NULL,
                                learning_notes TEXT,
                                completion_date DATE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users (id)
                            )
                        ''')
            
            conn.commit()
            conn.close()
            print("✅ Database structure verified/fixed")
            
        else:
            print("Database file doesn't exist, will be created on first run")
            
    except Exception as e:
        print(f"❌ Database fix error: {e}")

def create_azure_startup_script():
    """Create startup script for Azure"""
    print("🚀 Creating Azure Startup Script...")
    
    # Create a simple startup script
    startup_script = '''#!/bin/bash
echo "Starting AI Learning Tracker (Minimal Version)"
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files in directory: $(ls -la)"

# Set environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False

# Start the minimal app
python app_minimal.py
'''
    
    with open('startup_minimal.sh', 'w') as f:
        f.write(startup_script)
    
    print("✅ Created startup_minimal.sh")

def create_requirements_minimal():
    """Create minimal requirements file"""
    print("📦 Creating Minimal Requirements...")
    
    minimal_reqs = '''Flask==2.3.3
Werkzeug==2.3.7
gunicorn==21.2.0
'''
    
    with open('requirements_minimal.txt', 'w') as f:
        f.write(minimal_reqs)
    
    print("✅ Created requirements_minimal.txt")

def main():
    """Run the final fix"""
    print("🔧 Final Azure Fix - Minimal App Version")
    print("=" * 50)
    
    # Create minimal working version
    create_minimal_working_app()
    fix_database_permissions()
    create_azure_startup_script()
    create_requirements_minimal()
    
    print("\n✅ Minimal app version created!")
    print("\n🚀 To deploy the minimal version:")
    print("1. git add .")
    print("2. git commit -m 'Add minimal working version for Azure'")
    print("3. git push azure master")
    print("\n💡 Then in Azure Portal:")
    print("- Go to App Service > Configuration > General Settings")
    print("- Set Startup Command to: python app_minimal.py")
    print("- Save and restart the app")
    
    print("\n📋 Files created:")
    files = ['app_minimal.py', 'startup_minimal.sh', 'requirements_minimal.txt']
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (failed to create)")

if __name__ == "__main__":
    main()
