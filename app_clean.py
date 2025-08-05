"""
AI Learning Tracker - Clean Application Module
Fixed version with duplicate routes removed
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import hashlib
import threading
import time
import requests
from urllib.parse import urlparse
from collections import defaultdict
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enhanced security configuration
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=24)
})

# Database configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'ai_learning.db')
AZURE_CONNECTION_STRING = os.environ.get('AZURE_SQL_CONNECTION_STRING')

# Rate limiting
failed_attempts = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_ATTEMPTS = 5

# Session management
active_sessions = {}
session_lock = threading.Lock()

def get_db_connection():
    """Get database connection based on environment configuration"""
    try:
        # Always prefer Azure SQL in production
        if AZURE_CONNECTION_STRING and 'azure' in AZURE_CONNECTION_STRING.lower():
            print("🔄 Using Azure SQL Database...")
            import pyodbc
            
            # Parse connection string to get database name
            db_name = None
            for part in AZURE_CONNECTION_STRING.split(';'):
                if 'Database=' in part:
                    db_name = part.split('=')[1]
                    break
            
            print(f"📊 Connecting to Azure SQL Database: {db_name}")
            conn = pyodbc.connect(AZURE_CONNECTION_STRING)
            
            # Create a wrapper to make it behave like sqlite3.Row
            class AzureRow(dict):
                def __init__(self, cursor, row):
                    columns = [column[0] for column in cursor.description]
                    super().__init__(zip(columns, row))
                    
                def __getitem__(self, key):
                    if isinstance(key, int):
                        return list(self.values())[key]
                    return super().__getitem__(key)
            
            # Override execute method to return rows that behave like sqlite3.Row
            def enhanced_execute(query, params=()):
                cursor = conn.cursor()
                
                # Convert SQLite syntax to SQL Server syntax
                query = query.replace('?', '%s')
                query = query.replace('AUTOINCREMENT', 'IDENTITY(1,1)')
                query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'INT IDENTITY(1,1) PRIMARY KEY')
                query = query.replace('TEXT', 'NVARCHAR(MAX)')
                query = query.replace('REAL', 'FLOAT')
                query = query.replace('BLOB', 'VARBINARY(MAX)')
                
                cursor.execute(query, params)
                
                def create_fetchone_wrapper(cursor):
                    original_fetchone = cursor.fetchone
                    def fetchone():
                        row = original_fetchone()
                        return AzureRow(cursor, row) if row else None
                    return fetchone
                
                def create_fetchall_wrapper(cursor):
                    original_fetchall = cursor.fetchall
                    def fetchall():
                        rows = original_fetchall()
                        return [AzureRow(cursor, row) for row in rows] if rows else []
                    return fetchall
                
                cursor.fetchone = create_fetchone_wrapper(cursor)
                cursor.fetchall = create_fetchall_wrapper(cursor)
                return cursor
            
            conn.execute = enhanced_execute
            print("✅ Azure SQL Database connection established")
            return conn
            
    except Exception as e:
        print(f"⚠️  Azure SQL connection failed: {e}")
        print("🔄 Falling back to local SQLite database...")
    
    # Fallback to local SQLite
    print(f"📊 Using local SQLite database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_input(input_string):
    """Sanitize input to prevent XSS and injection attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters and patterns
    sanitized = re.sub(r'[<>"\']', '', str(input_string))
    sanitized = re.sub(r'(script|javascript|onload|onerror)', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def record_failed_attempt(ip_address, username=None):
    """Record a failed login attempt"""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO security_logs (ip_address, username, action, success, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip_address, username, 'login_attempt', False, request.headers.get('User-Agent')))
        conn.commit()
    except Exception as e:
        print(f"Error recording failed attempt: {e}")
    finally:
        conn.close()

def check_rate_limit(ip_address):
    """Check if IP address is rate limited"""
    current_time = time.time()
    
    # Clean old attempts
    failed_attempts[ip_address] = [
        attempt_time for attempt_time in failed_attempts[ip_address]
        if current_time - attempt_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if too many attempts
    if len(failed_attempts[ip_address]) >= MAX_ATTEMPTS:
        return False
    
    return True

def create_user_session(user_id, ip_address, user_agent):
    """Create a new user session"""
    session_token = secrets.token_urlsafe(32)
    
    conn = get_db_connection()
    try:
        # Invalidate old sessions for this user
        conn.execute('''
            UPDATE sessions 
            SET is_active = ? 
            WHERE user_id = ? AND is_active = ?
        ''', (False, user_id, True))
        
        # Create new session
        conn.execute('''
            INSERT INTO sessions (session_token, user_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (session_token, user_id, ip_address, user_agent))
        
        conn.commit()
        
        # Store in memory for quick access
        with session_lock:
            active_sessions[session_token] = {
                'user_id': user_id,
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }
        
        return session_token
        
    except Exception as e:
        print(f"Error creating session: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_current_user():
    """Get current user from session"""
    session_token = session.get('session_token')
    if not session_token:
        return None
    
    # Check memory first
    with session_lock:
        if session_token in active_sessions:
            session_data = active_sessions[session_token]
            session_data['last_activity'] = datetime.now()
        else:
            return None
    
    # Get user from database
    conn = get_db_connection()
    try:
        user_session = conn.execute('''
            SELECT s.*, u.username, u.level, u.points 
            FROM sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = ?
        ''', (session_token, True)).fetchone()
        
        if user_session:
            conn.execute('''
                UPDATE sessions 
                SET last_activity = ? 
                WHERE session_token = ?
            ''', (datetime.now(), session_token))
            conn.commit()
            
            return {
                'id': user_session['user_id'],
                'username': user_session['username'],
                'level': user_session['level'],
                'points': user_session['points']
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None
    finally:
        conn.close()

def invalidate_session(session_token):
    """Invalidate a user session"""
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE sessions 
            SET is_active = ? 
            WHERE session_token = ?
        ''', (False, session_token))
        conn.commit()
        
        # Remove from memory
        with session_lock:
            active_sessions.pop(session_token, None)
            
    except Exception as e:
        print(f"Error invalidating session: {e}")
    finally:
        conn.close()

@app.route('/')
def index():
    """Root route - redirect to appropriate page"""
    if session.get('session_token'):
        user = get_current_user()
        if user and user['username'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        client_ip = request.remote_addr
        
        # Check rate limiting
        if not check_rate_limit(client_ip):
            flash('Too many failed attempts. Please try again later.', 'error')
            return render_template('auth/login.html')
        
        # Validate user
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # Valid login - create session
            session_token = create_user_session(
                user['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            session['session_token'] = session_token
            session['user_id'] = user['id']
            session['username'] = username
            session.permanent = True
            
            flash(f'Welcome back, {username}!', 'success')
            if username == 'admin':
                return redirect('/admin')
            else:
                return redirect(url_for('dashboard'))
        else:
            # Invalid login
            record_failed_attempt(client_ip, username)
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session_token = session.get('session_token')
    if session_token:
        invalidate_session(session_token)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Dashboard with user statistics"""
    user = get_current_user()
    if not user:
        flash('Please log in to access this page.', 'info')
        return redirect(url_for('login'))
    
    # Get user data from database
    conn = get_db_connection()
    try:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        
        # Calculate stats
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']
        
        current_level = user_data['level'] if user_data else 'Beginner'
        
        # Get recent learning entries
        recent_learnings = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC 
            LIMIT 5
        ''', (user['id'],)).fetchall()
        
        # Get courses for current level
        all_courses = conn.execute('''
            SELECT c.*, COALESCE(uc.completed, 0) as completed 
            FROM courses c 
            LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
            WHERE c.level = ? 
            ORDER BY c.created_at DESC 
            LIMIT 10
        ''', (user['id'], current_level)).fetchall()
        
        # Separate completed and available courses
        completed_courses = [course for course in all_courses if course['completed']]
        available_courses = [course for course in all_courses if not course['completed']]
        
        return render_template('dashboard/index.html',
                             current_level=current_level,
                             learning_count=learning_count,
                             recent_learnings=recent_learnings,
                             available_courses=available_courses,
                             completed_courses=completed_courses)
    
    finally:
        conn.close()

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Get statistics
        user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        course_count = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        learning_count = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()['count']
        
        # Get recent users
        recent_users = conn.execute('''
            SELECT username, level, points, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        ''').fetchall()
        
        return render_template('admin/index.html',
                             user_count=user_count,
                             course_count=course_count,
                             learning_count=learning_count,
                             recent_users=recent_users)
    
    finally:
        conn.close()

@app.route('/create-admin-now')
def create_admin_now():
    """Emergency admin creation"""
    conn = get_db_connection()
    try:
        # Check if admin user already exists
        admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        
        if admin_user:
            return "<h2>❌ Admin user already exists!</h2><p>The admin user is already created in the database.</p><a href='/'>Go to Login</a>"
        
        # Create admin user with a secure password
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor = conn.execute('''
            INSERT INTO users (username, password_hash, level, points)
            VALUES (?, ?, ?, ?)
        ''', ('admin', password_hash, 'Expert', 1000))
        
        admin_id = cursor.lastrowid
        conn.commit()
        
        return f"<h2>✅ Admin user created successfully!</h2><p>Admin ID: {admin_id}</p><p>Username: admin</p><p>You can now login at <a href='/'>the login page</a></p>"
        
    except Exception as e:
        return f"<h2>❌ Error creating admin: {str(e)}</h2><a href='/create-admin-now'>Try Again</a>"
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
