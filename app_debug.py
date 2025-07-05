from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import traceback

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enhanced security configuration
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32)),
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=int(os.environ.get('SESSION_TIMEOUT', 3600))),
    SESSION_COOKIE_SECURE=True if os.environ.get('FLASK_ENV') == 'production' else False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Database configuration
DATABASE = 'ai_learning.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_safe():
    """Initialize the database with proper error handling"""
    try:
        conn = get_db_connection()
        
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learning entries table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS learning_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_global BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Courses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                provider TEXT,
                source TEXT,
                url TEXT,
                level TEXT,
                points INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_retired BOOLEAN DEFAULT 0,
                url_status TEXT DEFAULT 'unchecked',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User courses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT 0,
                completion_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id),
                UNIQUE(user_id, course_id)
            )
        ''')
        
        # Create admin user if not exists
        admin_hash = generate_password_hash('admin')
        try:
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def get_current_user():
    """Get current user from session"""
    if 'user_id' not in session:
        return None
    
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = get_current_user()
        if not user or user['username'] != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# Root route
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_level'] = user['level']
                flash(f'Welcome back, {username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@require_auth
def dashboard():
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        
        # Get user's learning entries count
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?', 
            (user['id'],)
        ).fetchone()['count']
        
        # Get user's completed courses count
        completed_count = conn.execute(
            'SELECT COUNT(*) as count FROM user_courses WHERE user_id = ? AND completed = 1', 
            (user['id'],)
        ).fetchone()['count']
        
        # Get recent learning entries
        recent_entries = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC 
            LIMIT 5
        ''', (user['id'],)).fetchall()
        
        conn.close()
        
        return render_template('dashboard/index.html', 
                             user=user,
                             learning_count=learning_count,
                             completed_count=completed_count,
                             recent_entries=recent_entries)
    except Exception as e:
        return f"<h1>Dashboard Error</h1><pre>{traceback.format_exc()}</pre>"

# Admin route with robust error handling
@app.route('/admin')
@require_admin
def admin():
    try:
        conn = get_db_connection()
        
        # Initialize with safe defaults
        stats = {
            'total_users': 0,
            'total_courses': 0,
            'total_global_learnings': 0,
            'recent_learnings': 0,
            'active_sessions': 0
        }
        
        try:
            # Get total users count
            result = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
            stats['total_users'] = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting user count: {e}")
        
        try:
            # Get total courses count
            result = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()
            stats['total_courses'] = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting course count: {e}")
        
        try:
            # Get total global learnings count
            result = conn.execute('SELECT COUNT(*) as count FROM learning_entries WHERE is_global = 1').fetchone()
            stats['total_global_learnings'] = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting global learnings count: {e}")
        
        try:
            # Get recent activity
            result = conn.execute('''
                SELECT COUNT(*) as count FROM learning_entries 
                WHERE date_added >= datetime('now', '-7 days')
            ''').fetchone()
            stats['recent_learnings'] = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting recent learnings: {e}")
        
        conn.close()
        
        return render_template('admin/index.html', **stats)
        
    except Exception as e:
        error_info = f"""
        <h1>Admin Dashboard Debug Info</h1>
        <h2>Error Details:</h2>
        <pre>{traceback.format_exc()}</pre>
        
        <h2>Database Tables Check:</h2>
        """
        
        try:
            conn = get_db_connection()
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            error_info += f"<p>Found tables: {[table['name'] for table in tables]}</p>"
            conn.close()
        except Exception as db_error:
            error_info += f"<p>Database error: {db_error}</p>"
        
        return error_info

# Simple admin routes
@app.route('/admin/courses')
@require_admin
def admin_courses():
    try:
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses ORDER BY created_at DESC').fetchall()
        conn.close()
        return render_template('admin/courses.html', courses=courses)
    except Exception as e:
        return f"<h1>Admin Courses Error</h1><pre>{traceback.format_exc()}</pre>"

# Simplified routes to prevent errors
@app.route('/admin/users')
@require_admin
def admin_users():
    return "<h1>Admin Users</h1><p>Feature coming soon</p>"

@app.route('/admin/add-user')
@require_admin
def admin_add_user():
    return "<h1>Add User</h1><p>Feature coming soon</p>"

@app.route('/admin/add-course')
@require_admin
def admin_add_course():
    return "<h1>Add Course</h1><p>Feature coming soon</p>"

@app.route('/admin/course-configs')
@require_admin
def admin_course_configs():
    return "<h1>Course Configs</h1><p>Feature coming soon</p>"

@app.route('/admin/populate-linkedin-courses', methods=['POST'])
@require_admin
def admin_populate_linkedin_courses():
    flash('LinkedIn course population feature is not implemented yet.', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/change-password')
@require_admin
def admin_change_password():
    return "<h1>Change Password</h1><p>Feature coming soon</p>"

@app.route('/admin/security')
@require_admin
def admin_security():
    return "<h1>Security</h1><p>Feature coming soon</p>"

@app.route('/admin/sessions')
@require_admin
def admin_sessions():
    return "<h1>Sessions</h1><p>Feature coming soon</p>"

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    return f"""
    <h1>Internal Server Error</h1>
    <h2>Debug Information:</h2>
    <pre>{traceback.format_exc()}</pre>
    <p><a href="/">Return to Home</a></p>
    """, 500

@app.errorhandler(404)
def not_found(error):
    return f"<h1>Page Not Found</h1><p>The requested page could not be found.</p><p><a href='/'>Return to Home</a></p>", 404

if __name__ == '__main__':
    # Initialize database on startup
    if init_db_safe():
        print("Database initialized successfully")
    else:
        print("Warning: Database initialization failed")
    
    app.run(debug=True)
