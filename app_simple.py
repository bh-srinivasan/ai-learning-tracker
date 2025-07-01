from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security configuration
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

def init_db():
    """Initialize the database with required tables"""
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
            user_selected_level TEXT DEFAULT 'Beginner',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            last_activity TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            session_token TEXT,
            password_reset_token TEXT,
            password_reset_expires TIMESTAMP,
            level_points INTEGER DEFAULT 0,
            level_updated_at TIMESTAMP
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
            custom_date DATE,
            tags TEXT,
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
            link TEXT,
            level TEXT,
            category TEXT,
            difficulty TEXT,
            points INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            is_retired BOOLEAN DEFAULT 0,
            url_status TEXT DEFAULT 'unchecked',
            last_url_check TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User course enrollments table
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
    
    # Create additional tables that might be referenced
    conn.execute('''
        CREATE TABLE IF NOT EXISTS level_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_name TEXT NOT NULL,
            points_required INTEGER NOT NULL
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS course_search_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            config TEXT NOT NULL
        )
    ''')
    
    # Create default users
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
    demo_password = os.environ.get('DEMO_PASSWORD', 'demo')
    
    admin_hash = generate_password_hash(admin_password)
    demo_hash = generate_password_hash(demo_password)
    
    try:
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('demo', demo_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Users already exist
    
    # Create default level settings
    try:
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Beginner', 0))
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Learner', 10))
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Intermediate', 25))
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Expert', 50))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Level settings already exist
    
    conn.close()

def get_current_user():
    """Get current user from session"""
    if 'user_id' not in session:
        return None
    
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
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

# Set up user context
@app.before_request
def load_logged_in_user():
    """Load user info into g for every request"""
    g.user = None
    if 'user_id' in session:
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            g.user = dict(user) if user else None
        except Exception:
            g.user = None
        finally:
            conn.close()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
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
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_auth
def dashboard():
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

@app.route('/admin')
@require_admin
def admin():
    try:
        conn = get_db_connection()
        
        # Get basic stats with error handling
        total_users = 0
        total_courses = 0
        total_global_learnings = 0
        recent_users = []
        
        try:
            total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE username != "admin"').fetchone()['count']
        except Exception:
            pass
            
        try:
            total_courses = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        except Exception:
            pass
            
        try:
            total_global_learnings = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()['count']
        except Exception:
            pass
            
        try:
            recent_users_data = conn.execute('''
                SELECT username, created_at 
                FROM users 
                WHERE username != "admin"
                ORDER BY created_at DESC 
                LIMIT 5
            ''').fetchall()
            
            recent_users = []
            for user in recent_users_data:
                recent_users.append({
                    'username': user['username'],
                    'level': 'Beginner',
                    'points': 0,
                    'created_at': user['created_at']
                })
        except Exception:
            pass
        
        conn.close()
        
        return render_template('admin/index.html',
                             total_users=total_users,
                             total_courses=total_courses,
                             total_global_learnings=total_global_learnings,
                             recent_users=recent_users)
    except Exception as e:
        return f"<h1>Admin Error</h1><p>Error: {str(e)}</p>"

# Test routes
@app.route('/test')
def test():
    return "Flask app is working!"

@app.route('/test/db')
def test_db():
    try:
        conn = get_db_connection()
        result = conn.execute('SELECT 1').fetchone()
        conn.close()
        return "Database connection successful!"
    except Exception as e:
        return f"Database error: {str(e)}"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
