from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import hashlib
import threading
import time
from collections import defaultdict
import re

app = Flask(__name__)

# Enhanced security configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),  # Session expires after 24 hours
    SESSION_COOKIE_SECURE=True if os.environ.get('FLASK_ENV') == 'production' else False,
    SESSION_COOKIE_HTTPONLY=True,  # Prevent XSS attacks
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
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
    
    # Users table - enhanced with session tracking
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
            password_reset_expires TIMESTAMP
        )
    ''')
    
    # User sessions table for active session tracking
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Session activity log
    conn.execute('''
        CREATE TABLE IF NOT EXISTS session_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            activity_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    ''')
    
    # Security events table for comprehensive logging
    conn.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create indexes for security events
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(ip_address)')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Indexes already exist
    
    # Level settings table for admin configuration
    conn.execute('''
        CREATE TABLE IF NOT EXISTS level_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_name TEXT UNIQUE NOT NULL,
            points_required INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default level settings
    try:
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Beginner', 0))
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Learner', 100))
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Intermediate', 250))
        conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', ('Expert', 500))
        conn.commit()
    except sqlite3.IntegrityError:
        # Settings already exist
        pass
    
    # Learning entries table - add custom_date field and make global for admin
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
    
    # Courses table - enhanced schema
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
            points INTEGER DEFAULT 0,
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
    
    # User personal courses table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_personal_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            course_url TEXT NOT NULL,
            description TEXT,
            completion_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User courses table (for dashboard course management)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            provider TEXT,
            url TEXT,
            level TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Update courses table structure to add missing columns
    try:
        conn.execute('ALTER TABLE courses ADD COLUMN provider TEXT')
        conn.execute('ALTER TABLE courses ADD COLUMN url TEXT')
        conn.execute('ALTER TABLE courses ADD COLUMN level TEXT')
        conn.execute('ALTER TABLE courses ADD COLUMN category TEXT')
        conn.execute('ALTER TABLE courses ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        conn.execute('ALTER TABLE courses ADD COLUMN points INTEGER DEFAULT 0')
        conn.execute('ALTER TABLE courses ADD COLUMN description TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Columns already exist or other error
        pass
    
    # Course search configurations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS course_search_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT UNIQUE NOT NULL,
            search_keywords TEXT NOT NULL,
            source TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default search configurations
    default_configs = [
        ('Artificial Intelligence', 'artificial intelligence,AI,machine learning,neural networks', 'LinkedIn Learning'),
        ('Machine Learning', 'machine learning,ML,deep learning,algorithms', 'LinkedIn Learning'),
        ('Microsoft Copilot', 'copilot,microsoft copilot,AI assistant', 'LinkedIn Learning'),
        ('Microsoft 365 Copilot', 'M365 copilot,office 365 copilot,microsoft 365 AI', 'LinkedIn Learning'),
        ('Data Science', 'data science,data analysis,python for data', 'LinkedIn Learning'),
        ('Computer Vision', 'computer vision,image processing,opencv', 'LinkedIn Learning'),
        ('Natural Language Processing', 'NLP,natural language processing,text analysis', 'LinkedIn Learning'),
        ('Cloud AI', 'azure AI,AWS AI,cloud machine learning', 'LinkedIn Learning'),
    ]
    
    for topic, keywords, source in default_configs:
        try:
            conn.execute('''
                INSERT INTO course_search_configs (topic_name, search_keywords, source)
                VALUES (?, ?, ?)
            ''', (topic, keywords, source))
        except sqlite3.IntegrityError:
            # Config already exists
            pass
    
    # Update existing users table to add missing columns if they don't exist
    columns_to_add = [
        ('points', 'INTEGER DEFAULT 0'),
        ('session_token', 'TEXT'),
        ('last_login', 'TIMESTAMP'),
        ('last_activity', 'TIMESTAMP'),
        ('login_count', 'INTEGER DEFAULT 0'),
        ('password_reset_token', 'TEXT'),
        ('password_reset_expires', 'TIMESTAMP')
    ]
    
    for column_name, column_def in columns_to_add:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
    
    # Update existing learning_entries table
    try:
        conn.execute('ALTER TABLE learning_entries ADD COLUMN custom_date DATE')
        conn.execute('ALTER TABLE learning_entries ADD COLUMN is_global BOOLEAN DEFAULT 0')
        conn.commit()
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Update existing courses table
    try:
        conn.execute('ALTER TABLE courses ADD COLUMN points INTEGER DEFAULT 0')
        conn.execute('ALTER TABLE courses ADD COLUMN description TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Create default users (admin and bharath)
    admin_hash = generate_password_hash('admin')
    bharath_hash = generate_password_hash('bharath')
    
    try:
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('bharath', bharath_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        # Users already exist
        pass
    
    conn.close()

# Session Management Functions
def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def create_user_session(user_id, ip_address=None, user_agent=None):
    """Create a new user session"""
    session_token = generate_session_token()
    expires_at = datetime.now() + app.config['PERMANENT_SESSION_LIFETIME']
    
    conn = get_db_connection()
    try:
        # Insert new session
        conn.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, expires_at, ip_address, user_agent))
        
        # Update user's login information (handle missing columns gracefully)
        try:
            # Try to update all columns
            conn.execute('''
                UPDATE users SET session_token = ?, last_login = ?, login_count = login_count + 1
                WHERE id = ?
            ''', (session_token, datetime.now(), user_id))
        except sqlite3.OperationalError as e:
            if 'session_token' in str(e):
                # session_token column doesn't exist, try without it
                try:
                    conn.execute('''
                        UPDATE users SET last_login = ?, login_count = login_count + 1
                        WHERE id = ?
                    ''', (datetime.now(), user_id))
                except sqlite3.OperationalError as e2:
                    if 'last_login' in str(e2):
                        # last_login column doesn't exist either, try just login_count
                        try:
                            conn.execute('''
                                UPDATE users SET login_count = login_count + 1
                                WHERE id = ?
                            ''', (user_id,))
                        except sqlite3.OperationalError:
                            # login_count column doesn't exist, skip user table update
                            pass
                    else:
                        # Different error, re-raise
                        raise e2
            elif 'last_login' in str(e):
                # last_login column doesn't exist, try without it
                try:
                    conn.execute('''
                        UPDATE users SET session_token = ?, login_count = login_count + 1
                        WHERE id = ?
                    ''', (session_token, user_id))
                except sqlite3.OperationalError as e2:
                    if 'login_count' in str(e2):
                        # login_count column doesn't exist either, just update session_token
                        conn.execute('''
                            UPDATE users SET session_token = ?
                            WHERE id = ?
                        ''', (session_token, user_id))
                    else:
                        # Different error, re-raise
                        raise e2
            else:
                # Different error, re-raise
                raise e
        
        conn.commit()
        
        # Log session activity
        log_session_activity(session_token, 'session_created', f'User {user_id} logged in', ip_address)
        
        return session_token
    finally:
        conn.close()

def validate_session(session_token, request=None):
    """Validate if a session is active and not expired"""
    if not session_token:
        return None
    
    conn = get_db_connection()
    try:
        session_data = conn.execute('''
            SELECT us.*, u.username, u.status 
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            WHERE us.session_token = ? AND us.is_active = 1 AND us.expires_at > ?
        ''', (session_token, datetime.now())).fetchone()
        
        if session_data:
            session_dict = dict(session_data)
            
            # Perform additional security checks if request is available
            if request:
                validate_session_security(request, session_dict)
            
            # Update last activity (handle missing column gracefully)
            try:
                conn.execute('''
                    UPDATE users SET last_activity = ? WHERE id = ?
                ''', (datetime.now(), session_dict['user_id']))
            except sqlite3.OperationalError:
                # last_activity column doesn't exist, skip this update
                pass
            conn.commit()
            
            return session_dict
        return None
    finally:
        conn.close()

def invalidate_session(session_token):
    """Invalidate a user session"""
    if not session_token:
        return
    
    conn = get_db_connection()
    try:
        # Mark session as inactive
        conn.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
        ''', (session_token,))
        
        # Clear session token from user (handle missing column gracefully)
        try:
            conn.execute('''
                UPDATE users SET session_token = NULL WHERE session_token = ?
            ''', (session_token,))
        except sqlite3.OperationalError:
            # session_token column doesn't exist, skip this step
            pass
        
        conn.commit()
        
        # Log session activity
        log_session_activity(session_token, 'session_invalidated', 'User logged out')
        
    finally:
        conn.close()

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    conn = get_db_connection()
    try:
        # Check if the user_sessions table exists
        tables = conn.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'
        ''').fetchone()
        
        if not tables:
            # Table doesn't exist yet, skip cleanup
            return
        
        # Get expired sessions
        expired_sessions = conn.execute('''
            SELECT session_token FROM user_sessions 
            WHERE expires_at < ? AND is_active = 1
        ''', (datetime.now(),)).fetchall()
        
        # Mark expired sessions as inactive
        conn.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE expires_at < ? AND is_active = 1
        ''', (datetime.now(),))
        
        # Clear expired session tokens from users (only if session_token column exists)
        try:
            conn.execute('''
                UPDATE users SET session_token = NULL 
                WHERE session_token IN (
                    SELECT session_token FROM user_sessions 
                    WHERE expires_at < ? AND is_active = 0
                )
            ''', (datetime.now(),))
        except sqlite3.OperationalError:
            # session_token column doesn't exist in users table, skip this step
            pass
        
        conn.commit()
        
        # Log cleanup activity
        for session in expired_sessions:
            log_session_activity(session['session_token'], 'session_expired', 'Session expired and cleaned up')
            
    except sqlite3.OperationalError as e:
        # Handle database schema issues gracefully
        print(f"Database schema issue in cleanup: {e}")
    finally:
        conn.close()

def log_session_activity(session_token, activity_type, activity_data=None, ip_address=None):
    """Log session activity"""
    conn = get_db_connection()
    try:
        # Check if session_activity table exists
        tables = conn.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='session_activity'
        ''').fetchone()
        
        if tables:
            conn.execute('''
                INSERT INTO session_activity (session_token, activity_type, activity_data, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (session_token, activity_type, activity_data, ip_address))
            conn.commit()
    except sqlite3.OperationalError as e:
        # Handle database schema issues gracefully
        print(f"Database schema issue in activity logging: {e}")
    finally:
        conn.close()

def get_user_sessions(user_id):
    """Get all active sessions for a user"""
    conn = get_db_connection()
    try:
        sessions = conn.execute('''
            SELECT * FROM user_sessions 
            WHERE user_id = ? AND is_active = 1 AND expires_at > ?
            ORDER BY created_at DESC
        ''', (user_id, datetime.now())).fetchall()
        return [dict(session) for session in sessions]
    finally:
        conn.close()

def invalidate_all_user_sessions(user_id, except_token=None):
    """Invalidate all sessions for a user, optionally except one"""
    conn = get_db_connection()
    try:
        if except_token:
            conn.execute('''
                UPDATE user_sessions SET is_active = 0 
                WHERE user_id = ? AND session_token != ?
            ''', (user_id, except_token))
        else:
            conn.execute('''
                UPDATE user_sessions SET is_active = 0 WHERE user_id = ?
            ''', (user_id,))
        
        # Update session token (handle missing column gracefully)
        try:
            conn.execute('''
                UPDATE users SET session_token = ? WHERE id = ?
            ''', (except_token, user_id))
        except sqlite3.OperationalError:
            # session_token column doesn't exist, skip this step
            pass
        
        conn.commit()
    finally:
        conn.close()

# Security configuration and rate limiting
# Rate limiting storage (in production, use Redis)
login_attempts = defaultdict(list)
failed_attempts = defaultdict(int)
blocked_ips = defaultdict(datetime)

# Security configuration
SECURITY_CONFIG = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 900,  # 15 minutes
    'PASSWORD_MIN_LENGTH': 6,
    'SESSION_TIMEOUT_WARNING': 300,  # 5 minutes
    'FAILED_LOGIN_WINDOW': 300,  # 5 minutes
    'SUSPICIOUS_ACTIVITY_THRESHOLD': 10,
    'ENABLE_CAPTCHA_AFTER_ATTEMPTS': 3
}

def is_ip_blocked(ip_address):
    """Check if IP address is currently blocked"""
    if ip_address in blocked_ips:
        if datetime.now() < blocked_ips[ip_address]:
            return True
        else:
            # Remove expired block
            del blocked_ips[ip_address]
    return False

def block_ip(ip_address, duration_minutes=15):
    """Block an IP address for specified duration"""
    blocked_ips[ip_address] = datetime.now() + timedelta(minutes=duration_minutes)
    log_security_event('ip_blocked', f'IP {ip_address} blocked for {duration_minutes} minutes')

def check_rate_limit(ip_address, action='login'):
    """Check if action is rate limited for IP"""
    now = datetime.now()
    window_start = now - timedelta(seconds=SECURITY_CONFIG['FAILED_LOGIN_WINDOW'])
    
    # Clean old attempts
    login_attempts[ip_address] = [
        attempt for attempt in login_attempts[ip_address] 
        if attempt > window_start
    ]
    
    # Check if exceeded max attempts
    if len(login_attempts[ip_address]) >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS']:
        block_ip(ip_address, SECURITY_CONFIG['LOCKOUT_DURATION'] // 60)
        return False
    
    return True

def record_failed_attempt(ip_address, username=None):
    """Record a failed login attempt"""
    login_attempts[ip_address].append(datetime.now())
    failed_attempts[ip_address] += 1
    
    log_security_event('failed_login', 
                      f'Failed login from IP {ip_address}' + 
                      (f' for user {username}' if username else ''))

def validate_password_strength(password):
    """Validate password meets security requirements"""
    if len(password) < SECURITY_CONFIG['PASSWORD_MIN_LENGTH']:
        return False, f"Password must be at least {SECURITY_CONFIG['PASSWORD_MIN_LENGTH']} characters long"
    
    # For now, keep simple validation to maintain existing login
    # In production, you might want stronger requirements
    return True, "Password is valid"

def sanitize_input(input_string):
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';]', '', str(input_string))
    return sanitized.strip()

def log_security_event(event_type, details, ip_address=None, user_id=None):
    """Log security events to database"""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO security_events (event_type, details, ip_address, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_type, details, ip_address, user_id, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"Error logging security event: {e}")
    finally:
        conn.close()

def detect_suspicious_activity(user_id, ip_address, user_agent):
    """Detect potentially suspicious user activity"""
    conn = get_db_connection()
    try:
        # Check for multiple IPs in short time
        recent_ips = conn.execute('''
            SELECT DISTINCT ip_address 
            FROM session_activity 
            WHERE session_token IN (
                SELECT session_token FROM user_sessions WHERE user_id = ?
            ) AND timestamp > datetime('now', '-1 hour')
        ''', (user_id,)).fetchall()
        
        if len(recent_ips) > 3:
            log_security_event('suspicious_activity', 
                              f'User {user_id} accessed from {len(recent_ips)} different IPs in 1 hour',
                              ip_address, user_id)
            return True
            
        # Check for rapid session creation
        recent_sessions = conn.execute('''
            SELECT COUNT(*) as count 
            FROM user_sessions 
            WHERE user_id = ? AND created_at > datetime('now', '-10 minutes')
        ''', (user_id,)).fetchone()['count']
        
        if recent_sessions > 3:
            log_security_event('suspicious_activity',
                              f'User {user_id} created {recent_sessions} sessions in 10 minutes',
                              ip_address, user_id)
            return True
            
    finally:
        conn.close()
    
    return False

def generate_csrf_token():
    """Generate CSRF token for forms"""
    return secrets.token_hex(16)

def validate_csrf_token(token, expected_token):
    """Validate CSRF token"""
    return token and expected_token and token == expected_token

# Flask before_request handler for session management and security
@app.before_request
def before_request():
    """Check session validity and security before each request"""
    # Clean up expired sessions periodically
    cleanup_expired_sessions()
    
    # Security checks for all requests
    client_ip = request.remote_addr
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        if request.endpoint and not request.endpoint.startswith('static'):
            flash('Access temporarily blocked due to security concerns.', 'error')
            return redirect(url_for('login'))
    
    # Log potentially suspicious requests
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent or len(user_agent) < 10:
        log_security_event('suspicious_request', f'Request with minimal/no user agent from {client_ip}', client_ip)
    
    # Check for common attack patterns in URL
    suspicious_patterns = ['<script', 'javascript:', 'vbscript:', '../', 'union select', 'drop table']
    request_url = request.url.lower()
    for pattern in suspicious_patterns:
        if pattern in request_url:
            log_security_event('suspicious_request', f'Suspicious URL pattern detected: {pattern}', client_ip)
            return "Bad Request", 400
    
    # Get session token from Flask session
    session_token = session.get('session_token')
    
    # Skip session validation for auth routes, static files, and health checks
    if request.endpoint and (request.endpoint in ['login', 'logout', 'static', 'index', 'security_health', 'test_page', 'debug_session']):
        return
    
    # Validate session
    if session_token:
        session_data = validate_session(session_token, request)
        if session_data:
            # Store user info in g for easy access
            g.user = {
                'id': session_data['user_id'],
                'username': session_data['username'],
                'status': session_data['status']
            }
            g.session_token = session_token
            
            # Additional security check for admin routes
            if request.endpoint and request.endpoint.startswith('admin'):
                if session_data['username'] != 'admin':
                    log_security_event('unauthorized_admin_access', 
                                     f'Non-admin user {session_data["username"]} attempted admin access', 
                                     client_ip, session_data['user_id'])
                    flash('Admin privileges required.', 'error')
                    return redirect(url_for('dashboard'))
            
            # Log page access for non-static requests
            if request.endpoint and not request.endpoint.startswith('static'):
                log_session_activity(session_token, 'page_access', 
                                   f"Accessed {request.endpoint}", client_ip)
        else:
            # Invalid session, clear it and redirect to login
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            try:
                return redirect(url_for('login'))
            except:
                return render_template('auth/login.html'), 401
    else:
        # No session, redirect to login
        flash('Please log in to access this page.', 'info')
        try:
            return redirect(url_for('login'))
        except:
            return render_template('auth/login.html'), 401

# Authentication decorators
def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_token' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        # Validate session
        user_data = validate_session(session['session_token'], request)
        if not user_data:
            flash('Your session has expired. Please log in again.', 'error')
            session.clear()
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_token' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        # Validate session
        user_data = validate_session(session['session_token'], request)
        if not user_data:
            flash('Your session has expired. Please log in again.', 'error')
            session.clear()
            return redirect(url_for('login'))
        
        # Check if user is admin
        if not user_data.get('is_admin', False):
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get current user
def get_current_user():
    """Get current user from session"""
    if hasattr(g, 'user'):
        return g.user
    return None

def require_login(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user['username'] != 'admin':
            flash('Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/extend-session', methods=['POST'])
def extend_session():
    """Extend the current user session"""
    session_token = session.get('session_token')
    
    if not session_token:
        return {'success': False, 'message': 'No active session'}, 401
    
    # Validate and extend session
    session_data = validate_session(session_token)
    if session_data:
        # Update session expiry
        new_expires_at = datetime.now() + app.config['PERMANENT_SESSION_LIFETIME']
        
        conn = get_db_connection()
        try:
            conn.execute('''
                UPDATE user_sessions SET expires_at = ? 
                WHERE session_token = ? AND is_active = 1
            ''', (new_expires_at, session_token))
            
            conn.execute('''
                UPDATE users SET last_activity = ? 
                WHERE id = ?
            ''', (datetime.now(), session_data['user_id']))
            
            conn.commit()
            
            # Log session extension
            log_session_activity(session_token, 'session_extended', 'Session extended by user')
            
            return {'success': True, 'message': 'Session extended', 'expires_at': new_expires_at.isoformat()}
        finally:
            conn.close()
    else:
        return {'success': False, 'message': 'Invalid session'}, 401

@app.route('/session-status')
def session_status():
    """Get current session status"""
    session_token = session.get('session_token')
    
    if not session_token:
        return {'active': False}
    
    session_data = validate_session(session_token)
    if session_data:
        return {
            'active': True,
            'user': session_data['username'],
            'expires_at': session_data['expires_at']
        }
    else:
        return {'active': False}

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy (basic)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    
    # Strict Transport Security (HTTPS only)
    if request.is_secure or app.config.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Additional session security validation
def validate_session_security(request, session_data):
    """Additional security checks for session validation"""
    # Check if IP address matches (optional, can be disabled for mobile users)
    stored_ip = session_data.get('ip_address')
    current_ip = request.remote_addr
    
    # For now, we'll log IP changes but not invalidate sessions
    # This helps with mobile users switching networks
    if stored_ip and stored_ip != current_ip:
        log_session_activity(session_data['session_token'], 'ip_change', 
                           f'IP changed from {stored_ip} to {current_ip}', current_ip)
    
    # Check user agent (basic check)
    stored_agent = session_data.get('user_agent')
    current_agent = request.headers.get('User-Agent')
    
    if stored_agent and current_agent:
        # Extract browser info for comparison (simplified)
        def extract_browser_info(ua):
            if not ua:
                return ''
            # Simple extraction of major browser info
            for browser in ['Chrome', 'Firefox', 'Safari', 'Edge']:
                if browser in ua:
                    return browser
            return 'Unknown'
        
        stored_browser = extract_browser_info(stored_agent)
        current_browser = extract_browser_info(current_agent)
        
        if stored_browser != current_browser and stored_browser != 'Unknown':
            log_session_activity(session_data['session_token'], 'browser_change', 
                               f'Browser changed from {stored_browser} to {current_browser}')
    
    return True  # Session is valid

# Session cleanup scheduler
def session_cleanup_scheduler():
    """Background thread to periodically clean up expired sessions"""
    while True:
        try:
            cleanup_expired_sessions()
            time.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Session cleanup error: {e}")
            time.sleep(3600)  # Continue after error

# Start session cleanup thread
cleanup_thread = threading.Thread(target=session_cleanup_scheduler, daemon=True)
cleanup_thread.start()

# Initialize database on startup
init_db()

# Temporarily comment out blueprints to fix circular import
# TODO: Re-enable after fixing circular imports
# from auth.routes import auth_bp
# from dashboard.routes import dashboard_bp
# from learnings.routes import learnings_bp
# from admin.routes import admin_bp

# app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
# app.register_blueprint(learnings_bp, url_prefix='/learnings')
# app.register_blueprint(admin_bp, url_prefix='/admin')

# Error handlers for security
@app.errorhandler(400)
def bad_request(error):
    return render_template('auth/login.html'), 400

@app.errorhandler(403)
def forbidden(error):
    return render_template('auth/login.html'), 403

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return render_template('auth/login.html'), 429

# Security monitoring route
@app.route('/security-health')
def security_health():
    """Security health check endpoint (for monitoring)"""
    return {
        'status': 'active',
        'security_features': [
            'rate_limiting',
            'session_management', 
            'input_sanitization',
            'security_headers',
            'activity_logging'
        ],
        'timestamp': datetime.now().isoformat()
    }

# Root route - redirect to login
@app.route('/')
def index():
    """Root route - redirect to appropriate page"""
    if session.get('session_token'):
        # Check if user is admin and redirect to admin dashboard
        user = get_current_user()
        if user and user['username'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Simple login route for testing
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login route for testing security features"""
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
            session.permanent = True
            
            flash(f'Welcome back, {username}!', 'success')
            # Redirect admin users to admin dashboard
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
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
    print(f"Dashboard route - User: {user}")  # Debug
    if not user:
        flash('Please log in to access this page.', 'info')
        return redirect(url_for('login'))
    
    # Get user data from database
    conn = get_db_connection()
    try:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        print(f"Dashboard route - User data: {dict(user_data) if user_data else None}")  # Debug
        
        # Calculate stats
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']
        
        current_level = user_data['level'] if user_data else 'Beginner'
        user_points = user_data['points'] if user_data else 0
        
        # Calculate next level info
        level_mapping = {'Beginner': 0, 'Learner': 100, 'Intermediate': 250, 'Expert': 500}
        next_level = 'Expert'
        points_needed = 0
        
        for level, required_points in level_mapping.items():
            if user_points < required_points:
                next_level = level
                points_needed = required_points - user_points
                break
        
        next_level_info = f"{points_needed} pts to {next_level}" if points_needed > 0 else "Max Level!"
        
        # Calculate progress percentage
        current_points = user_points
        next_level_points = next((points for level, points in level_mapping.items() if points > user_points), 500)
        prev_level_points = max([points for points in level_mapping.values() if points <= user_points], default=0)
        
        if next_level_points > prev_level_points:
            progress_percentage = ((current_points - prev_level_points) / (next_level_points - prev_level_points)) * 100
        else:
            progress_percentage = 100
        
        # Get recent learning entries
        recent_learnings = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC 
            LIMIT 5
        ''', (user['id'],)).fetchall()
        
        # Get recommended courses with completion status
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
                             user_points=user_points,
                             next_level_info=next_level_info,
                             progress_percentage=int(progress_percentage),
                             learning_count=learning_count,
                             recent_learnings=recent_learnings,
                             available_courses=available_courses,
                             completed_courses=completed_courses)
    
    finally:
        conn.close()

# Context processor to provide user info to all templates
@app.context_processor
def inject_user():
    """Inject user information into template context"""
    user = get_current_user()
    if user:
        # Get user level from database
        conn = get_db_connection()
        try:
            user_data = conn.execute('SELECT level FROM users WHERE id = ?', (user['id'],)).fetchone()
            user_level = user_data['level'] if user_data else 'Beginner'
        except:
            user_level = 'Beginner'
        finally:
            conn.close()
            
        return {
            'session': {
                'username': user['username'],
                'user_level': user_level,
                'user_id': user['id']
            }
        }
    return {'session': {}}

# Basic routes for navigation
@app.route('/learnings')
def learnings():
    """Learning entries list"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get user's learning entries
    conn = get_db_connection()
    try:
        learnings = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC
        ''', (user['id'],)).fetchall()
        
        return render_template('learnings/index.html', learnings=learnings)
    finally:
        conn.close()

@app.route('/add-learning')
def add_learning():
    """Add learning entry"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('learnings/add.html')

@app.route('/my-courses')
def my_courses():
    """My courses page - shows completed courses and recommended courses"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get filter parameters
    provider_filter = request.args.get('provider', '')
    level_filter = request.args.get('level', '')
    date_filter = request.args.get('date_filter', '')
    search_query = request.args.get('search', '')
    
    conn = get_db_connection()
    try:
        # Base query for completed courses (without provider filter for now)
        completed_query = '''
            SELECT c.*, uc.completed, uc.completion_date, 'system' as course_type
            FROM courses c 
            INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
        '''
        completed_params = [user['id']]
        
        # Apply filters to completed courses (skip provider/level if columns don't exist)
        if search_query:
            completed_query += ' AND (c.title LIKE ? OR c.description LIKE ?)'
            completed_params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        # Date filtering for completed courses
        if date_filter:
            if date_filter == 'today':
                completed_query += ' AND DATE(uc.completion_date) = DATE("now")'
            elif date_filter == 'week':
                completed_query += ' AND DATE(uc.completion_date) >= DATE("now", "-7 days")'
            elif date_filter == 'month':
                completed_query += ' AND DATE(uc.completion_date) >= DATE("now", "-30 days")'
        
        completed_query += ' ORDER BY uc.completion_date DESC'
        completed_courses = conn.execute(completed_query, completed_params).fetchall()
        
        # Base query for recommended courses (without provider/level filter for now)
        user_level = user.get('level', 'Beginner')
        recommended_query = '''
            SELECT c.*, COALESCE(uc.completed, 0) as completed, 'recommended' as course_type
            FROM courses c 
            LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
            WHERE (uc.completed IS NULL OR uc.completed = 0)
        '''
        recommended_params = [user['id']]
        
        # Apply search filter to recommended courses
        if search_query:
            recommended_query += ' AND (c.title LIKE ? OR c.description LIKE ?)'
            recommended_params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        recommended_query += ' ORDER BY c.created_at DESC'
        recommended_courses = conn.execute(recommended_query, recommended_params).fetchall()
        
        # Get available filter options (empty for now due to missing columns)
        providers = []
        levels = []
        
        return render_template('dashboard/my_courses.html', 
                             completed_courses=completed_courses,
                             recommended_courses=recommended_courses,
                             providers=providers,
                             levels=levels,
                             current_filters={
                                 'provider': provider_filter,
                                 'level': level_filter,
                                 'date_filter': date_filter,
                                 'search': search_query
                             })
    finally:
        conn.close()

@app.route('/profile')
def profile():
    """User profile page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get user profile data
    conn = get_db_connection()
    try:
        user_data = conn.execute('''
            SELECT * FROM users WHERE id = ?
        ''', (user['id'],)).fetchone()
        
        return render_template('dashboard/profile.html', user=user_data)
    finally:
        conn.close()

# Admin routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - shows same as main dashboard plus admin stats"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
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
        user_points = user_data['points'] if user_data else 0
        
        # Calculate next level info
        level_mapping = {'Beginner': 0, 'Learner': 100, 'Intermediate': 250, 'Expert': 500}
        next_level = 'Expert'
        points_needed = 0
        
        for level, required_points in level_mapping.items():
            if user_points < required_points:
                next_level = level
                points_needed = required_points - user_points
                break
        
        next_level_info = f"{points_needed} pts to {next_level}" if points_needed > 0 else "Max Level!"
        
        # Calculate progress percentage
        current_points = user_points
        next_level_points = next((points for level, points in level_mapping.items() if points > user_points), 500)
        prev_level_points = max([points for points in level_mapping.values() if points <= user_points], default=0)
        
        if next_level_points > prev_level_points:
            progress_percentage = ((current_points - prev_level_points) / (next_level_points - prev_level_points)) * 100
        else:
            progress_percentage = 100
        
        # Get recent learning entries
        recent_learnings = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC 
            LIMIT 5
        ''', (user['id'],)).fetchall()
        
        # Get recommended courses with completion status
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
        
        # Admin-specific stats
        total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        total_courses = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        total_global_learnings = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()['count']
        active_sessions = conn.execute('SELECT COUNT(*) as count FROM user_sessions WHERE is_active = 1').fetchone()['count']
        
        # Get recent users for the dashboard
        recent_users = conn.execute('''
            SELECT username, level, points, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        ''').fetchall()
        
        return render_template('admin/index.html',
                             current_level=current_level,
                             user_points=user_points,
                             next_level_info=next_level_info,
                             progress_percentage=int(progress_percentage),
                             learning_count=learning_count,
                             recent_learnings=recent_learnings,
                             available_courses=available_courses,
                             completed_courses=completed_courses,
                             total_users=total_users,
                             total_courses=total_courses,
                             total_global_learnings=total_global_learnings,
                             active_sessions=active_sessions,
                             recent_users=recent_users)
    
    finally:
        conn.close()

@app.route('/admin/users')
def admin_users():
    """Admin user management"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all users
    conn = get_db_connection()
    try:
        users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        return render_template('admin/users.html', users=users)
    finally:
        conn.close()

@app.route('/admin/sessions')
def admin_sessions():
    """Admin session management"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get session data
    conn = get_db_connection()
    try:
        sessions = conn.execute('''
            SELECT us.*, u.username 
            FROM user_sessions us 
            JOIN users u ON us.user_id = u.id 
            WHERE us.is_active = 1 
            ORDER BY us.created_at DESC
        ''').fetchall()
        return render_template('admin/sessions.html', sessions=sessions)
    finally:
        conn.close()

@app.route('/admin/security')
def admin_security():
    """Admin security dashboard"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get security events
    conn = get_db_connection()
    try:
        events = conn.execute('''
            SELECT * FROM security_events 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''').fetchall()
        return render_template('admin/security.html', events=events)
    finally:
        conn.close()

@app.route('/admin/courses')
def admin_courses():
    """Admin course management"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get courses
    conn = get_db_connection()
    try:
        courses = conn.execute('SELECT * FROM courses ORDER BY created_at DESC').fetchall()
        return render_template('admin/courses.html', courses=courses)
    finally:
        conn.close()

@app.route('/admin/course-configs')
def admin_course_configs():
    """Admin course search configurations"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get course configs
    conn = get_db_connection()
    try:
        configs = conn.execute('SELECT * FROM course_search_configs ORDER BY created_at DESC').fetchall()
        return render_template('admin/course_search_configs.html', configs=configs)
    finally:
        conn.close()

@app.route('/admin/settings')
def admin_settings():
    """Admin settings"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get level settings and system settings
    conn = get_db_connection()
    try:
        level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        
        # Get system statistics
        system_stats = {
            'total_users': conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
            'active_users': conn.execute('SELECT COUNT(*) as count FROM users WHERE status = "active"').fetchone()['count'],
            'total_courses': conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count'],
            'total_learnings': conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()['count'],
            'active_sessions': conn.execute('SELECT COUNT(*) as count FROM user_sessions WHERE is_active = 1').fetchone()['count'],
        }
        
        # Get security settings
        security_settings = {
            'max_login_attempts': SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS'],
            'lockout_duration': SECURITY_CONFIG['LOCKOUT_DURATION'] // 60,  # Convert to minutes
            'password_min_length': SECURITY_CONFIG['PASSWORD_MIN_LENGTH'],
            'session_timeout': app.config['PERMANENT_SESSION_LIFETIME'].total_seconds() // 3600,  # Convert to hours
        }
        
        return render_template('admin/settings.html', 
                             level_settings=level_settings,
                             system_stats=system_stats,
                             security_settings=security_settings)
    finally:
        conn.close()

@app.route('/admin/settings/update-level', methods=['POST'])
@require_admin
def admin_update_level_settings():
    """Update level settings (admin only)"""
    level_name = sanitize_input(request.form.get('level_name'))
    points_required = request.form.get('points_required')
    
    if not level_name or not points_required:
        flash('Level name and points are required.', 'error')
        return redirect(url_for('admin_settings'))
    
    try:
        points_required = int(points_required)
    except ValueError:
        flash('Points must be a valid number.', 'error')
        return redirect(url_for('admin_settings'))
    
    conn = get_db_connection()
    try:
        # Check if level exists
        existing = conn.execute('SELECT id FROM level_settings WHERE level_name = ?', (level_name,)).fetchone()
        
        if existing:
            # Update existing level
            conn.execute('UPDATE level_settings SET points_required = ? WHERE level_name = ?', 
                        (points_required, level_name))
            flash(f'Level {level_name} updated successfully!', 'success')
        else:
            # Create new level
            conn.execute('INSERT INTO level_settings (level_name, points_required) VALUES (?, ?)', 
                        (level_name, points_required))
            flash(f'Level {level_name} created successfully!', 'success')
        
        conn.commit()
    except Exception as e:
        flash(f'Error updating level settings: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_settings'))

# Admin User Management Routes
@app.route('/admin/add-user', methods=['GET', 'POST'])
@require_admin
def admin_add_user():
    """Add a new user (admin only)"""
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        password = request.form.get('password')
        level = sanitize_input(request.form.get('level', 'Beginner'))
        status = sanitize_input(request.form.get('status', 'active'))
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('admin/add_user.html')
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('admin/add_user.html')
        
        conn = get_db_connection()
        try:
            # Check if username already exists
            existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing:
                flash('Username already exists.', 'error')
                return render_template('admin/add_user.html')
            
            # Create new user
            password_hash = generate_password_hash(password)
            conn.execute('''
                INSERT INTO users (username, password_hash, level, status, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (username, password_hash, level, status))
            conn.commit()
            
            flash(f'User "{username}" created successfully!', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin/add_user.html')

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@require_admin
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    conn = get_db_connection()
    try:
        # Check if user exists and is not admin
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        if user['username'] == 'admin':
            flash('Cannot delete admin user.', 'error')
            return redirect(url_for('admin_users'))
        
        # Delete user and related data
        conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM user_personal_courses WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        flash(f'User "{user["username"]}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/pause-user/<int:user_id>', methods=['POST'])
@require_admin
def admin_pause_user(user_id):
    """Pause/unpause a user (admin only)"""
    conn = get_db_connection()
    try:
        # Get current user status
        user = conn.execute('SELECT username, status FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        if user['username'] == 'admin':
            flash('Cannot pause admin user.', 'error')
            return redirect(url_for('admin_users'))
        
        # Toggle status
        new_status = 'paused' if user['status'] == 'active' else 'active'
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        
        # If pausing, invalidate all sessions
        if new_status == 'paused':
            conn.execute('UPDATE user_sessions SET is_active = 0 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        
        action = 'paused' if new_status == 'paused' else 'activated'
        flash(f'User "{user["username"]}" {action} successfully!', 'success')
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

# Admin Course Management Routes
@app.route('/admin/add-course', methods=['GET', 'POST'])
@require_admin
def admin_add_course():
    """Add a new course (admin only)"""
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title'))
        description = sanitize_input(request.form.get('description'))
        provider = sanitize_input(request.form.get('provider'))
        source = sanitize_input(request.form.get('source'))
        url = sanitize_input(request.form.get('url'))
        link = sanitize_input(request.form.get('link'))
        level = sanitize_input(request.form.get('level'))
        category = sanitize_input(request.form.get('category'))
        points = request.form.get('points', 0)
        
        if not title or not description:
            flash('Title and description are required.', 'error')
            return render_template('admin/add_course.html')
        
        try:
            points = int(points) if points else 0
        except ValueError:
            points = 0
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO courses (title, description, provider, source, url, link, level, category, points, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (title, description, provider, source, url, link, level, category, points))
            conn.commit()
            flash('Course added successfully!', 'success')
            return redirect(url_for('admin_courses'))
        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin/add_course.html')

@app.route('/admin/edit-course/<int:course_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_course(course_id):
    """Edit a course (admin only)"""
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            title = sanitize_input(request.form.get('title'))
            description = sanitize_input(request.form.get('description'))
            provider = sanitize_input(request.form.get('provider'))
            source = sanitize_input(request.form.get('source'))
            url = sanitize_input(request.form.get('url'))
            link = sanitize_input(request.form.get('link'))
            level = sanitize_input(request.form.get('level'))
            category = sanitize_input(request.form.get('category'))
            points = request.form.get('points', 0)
            
            if not title or not description:
                flash('Title and description are required.', 'error')
                return redirect(url_for('admin_edit_course', course_id=course_id))
            
            try:
                points = int(points) if points else 0
            except ValueError:
                points = 0
            
            conn.execute('''
                UPDATE courses 
                SET title=?, description=?, provider=?, source=?, url=?, link=?, level=?, category=?, points=?, updated_at=datetime('now')
                WHERE id=?
            ''', (title, description, provider, source, url, link, level, category, points, course_id))
            conn.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('admin_courses'))
        
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('admin_courses'))
        
        return render_template('admin/edit_course.html', course=course)
    finally:
        conn.close()

@app.route('/admin/delete-course/<int:course_id>', methods=['POST'])
@require_admin
def admin_delete_course(course_id):
    """Delete a course (admin only)"""
    conn = get_db_connection()
    try:
        # Delete related records first
        conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/populate-linkedin-courses', methods=['POST'])
@require_admin
def admin_populate_linkedin_courses():
    """Populate courses with LinkedIn Learning AI courses (admin only)"""
    # Sample LinkedIn Learning AI courses
    linkedin_courses = [
        {
            'title': 'Introduction to Artificial Intelligence',
            'description': 'Learn the fundamentals of AI and machine learning',
            'provider': 'LinkedIn Learning',
            'source': 'LinkedIn Learning',
            'url': 'https://www.linkedin.com/learning/introduction-to-artificial-intelligence',
            'link': 'https://www.linkedin.com/learning/introduction-to-artificial-intelligence',
            'level': 'Beginner',
            'category': 'AI Fundamentals',
            'points': 50
        },
        {
            'title': 'Machine Learning with Python',
            'description': 'Master machine learning using Python libraries',
            'provider': 'LinkedIn Learning',
            'source': 'LinkedIn Learning',
            'url': 'https://www.linkedin.com/learning/machine-learning-with-python',
            'link': 'https://www.linkedin.com/learning/machine-learning-with-python',
            'level': 'Intermediate',
            'category': 'Machine Learning',
            'points': 100
        },
        {
            'title': 'Deep Learning Foundations',
            'description': 'Understanding deep learning and neural networks',
            'provider': 'LinkedIn Learning',
            'source': 'LinkedIn Learning',
            'url': 'https://www.linkedin.com/learning/deep-learning-foundations',
            'link': 'https://www.linkedin.com/learning/deep-learning-foundations',
            'level': 'Advanced',
            'category': 'Deep Learning',
            'points': 150
        },
        {
            'title': 'Microsoft Copilot for Developers',
            'description': 'Learn to use Microsoft Copilot effectively in development',
            'provider': 'LinkedIn Learning',
            'source': 'LinkedIn Learning',
            'url': 'https://www.linkedin.com/learning/microsoft-copilot-for-developers',
            'link': 'https://www.linkedin.com/learning/microsoft-copilot-for-developers',
            'level': 'Intermediate',
            'category': 'AI Tools',
            'points': 75
        }
    ]
    
    conn = get_db_connection()
    try:
        added_count = 0
        for course in linkedin_courses:
            # Check if course already exists
            existing = conn.execute(
                'SELECT id FROM courses WHERE title = ? AND provider = ?',
                (course['title'], course['provider'])
            ).fetchone()
            
            if not existing:
                conn.execute('''
                    INSERT INTO courses (title, description, provider, source, url, link, level, category, points, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (course['title'], course['description'], course['provider'], course['source'],
                     course['url'], course['link'], course['level'], course['category'], course['points']))
                added_count += 1
        
        conn.commit()
        flash(f'Added {added_count} LinkedIn Learning courses!', 'success')
    except Exception as e:
        flash(f'Error adding LinkedIn courses: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/search-and-import-courses', methods=['POST'])
@require_admin
def admin_search_and_import_courses():
    """Search and import courses from external sources (admin only)"""
    search_term = sanitize_input(request.form.get('search_term', ''))
    source = sanitize_input(request.form.get('source', 'manual'))
    
    if not search_term:
        flash('Search term is required.', 'error')
        return redirect(url_for('admin_course_configs'))
    
    # This would integrate with actual course APIs
    # For now, just create a sample course based on search
    conn = get_db_connection()
    try:
        sample_course = {
            'title': f'AI Course: {search_term}',
            'description': f'Comprehensive course covering {search_term} in artificial intelligence',
            'provider': f'{source.title()} Learning',
            'source': f'{source.title()} Learning',
            'url': f'https://example.com/courses/{search_term.lower().replace(" ", "-")}',
            'link': f'https://example.com/courses/{search_term.lower().replace(" ", "-")}',
            'level': 'Intermediate',
            'category': 'AI & Machine Learning',
            'points': 100
        }
        
        conn.execute('''
            INSERT OR IGNORE INTO courses (title, description, provider, source, url, link, level, category, points, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (sample_course['title'], sample_course['description'], sample_course['provider'],
             sample_course['source'], sample_course['url'], sample_course['link'], 
             sample_course['level'], sample_course['category'], sample_course['points']))
        conn.commit()
        flash(f'Course "{sample_course["title"]}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_course_configs'))

@app.route('/admin/export-courses')
@require_admin
def admin_export_courses():
    """Export courses to CSV (admin only)"""
    import csv
    from io import StringIO
    from flask import Response
    
    conn = get_db_connection()
    try:
        courses = conn.execute('SELECT * FROM courses ORDER BY created_at DESC').fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Title', 'Description', 'Provider', 'Source', 'URL', 'Level', 'Category', 'Points', 'Created At'])
        
        # Write course data
        for course in courses:
            writer.writerow([
                course['id'], course['title'], course['description'], 
                course['provider'], course['source'], course['url'],
                course['level'], course['category'], course['points'], course['created_at']
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=courses.csv'}
        )
    finally:
        conn.close()

@app.route('/dashboard/add-course', methods=['GET', 'POST'])
@require_auth
def dashboard_add_course():
    """Add a new course for the current user"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title'))
        description = sanitize_input(request.form.get('description'))
        provider = sanitize_input(request.form.get('provider'))
        url = sanitize_input(request.form.get('url'))
        level = sanitize_input(request.form.get('level'))
        category = sanitize_input(request.form.get('category'))
        
        if title and description:
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO user_personal_courses (user_id, title, description, source, course_url, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (user['id'], title, description, provider or 'Personal', url or ''))
                conn.commit()
                flash('Course added successfully!', 'success')
                return redirect(url_for('dashboard_my_courses'))
            except Exception as e:
                flash(f'Error adding course: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Title and description are required.', 'error')
    
    return render_template('dashboard/add_course.html')

@app.route('/dashboard/my-courses')
@require_auth
def dashboard_my_courses():
    """Display user's courses"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get filter parameters
    provider_filter = request.args.get('provider', '')
    level_filter = request.args.get('level', '')
    date_filter = request.args.get('date_filter', '')
    search_query = request.args.get('search', '')
        
    conn = get_db_connection()
    try:
        # Base query for completed courses (without provider filter for now)
        completed_query = '''
            SELECT c.*, uc.completed, uc.completion_date, 'system' as course_type
            FROM courses c 
            INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
        '''
        completed_params = [user['id']]
        
        # Apply filters to completed courses (skip provider/level if columns don't exist)
        if search_query:
            completed_query += ' AND (c.title LIKE ? OR c.description LIKE ?)'
            completed_params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        # Date filtering for completed courses
        if date_filter:
            if date_filter == 'today':
                completed_query += ' AND DATE(uc.completion_date) = DATE("now")'
            elif date_filter == 'week':
                completed_query += ' AND DATE(uc.completion_date) >= DATE("now", "-7 days")'
            elif date_filter == 'month':
                completed_query += ' AND DATE(uc.completion_date) >= DATE("now", "-30 days")'
        
        completed_query += ' ORDER BY uc.completion_date DESC'
        completed_courses = conn.execute(completed_query, completed_params).fetchall()
        
        # Base query for recommended courses (without provider/level filter for now)
        user_level = user.get('level', 'Beginner')
        recommended_query = '''
            SELECT c.*, COALESCE(uc.completed, 0) as completed, 'recommended' as course_type
            FROM courses c 
            LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
            WHERE (uc.completed IS NULL OR uc.completed = 0)
        '''
        recommended_params = [user['id']]
        
        # Apply search filter to recommended courses
        if search_query:
            recommended_query += ' AND (c.title LIKE ? OR c.description LIKE ?)'
            recommended_params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        recommended_query += ' ORDER BY c.created_at DESC'
        recommended_courses = conn.execute(recommended_query, recommended_params).fetchall()
        
        # Get available filter options (empty for now due to missing columns)
        providers = []
        levels = []
        
        return render_template('dashboard/my_courses.html', 
                             completed_courses=completed_courses,
                             recommended_courses=recommended_courses,
                             providers=providers,
                             levels=levels,
                             current_filters={
                                 'provider': provider_filter,
                                 'level': level_filter,
                                 'date_filter': date_filter,
                                 'search': search_query
                             })
    finally:
        conn.close()

@app.route('/dashboard/edit-course/<int:course_id>', methods=['GET', 'POST'])
@require_auth
def dashboard_edit_course(course_id):
    """Edit user's course"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            title = sanitize_input(request.form.get('title'))
            description = sanitize_input(request.form.get('description'))
            provider = sanitize_input(request.form.get('provider'))
            url = sanitize_input(request.form.get('url'))
            
            if title and description:
                conn.execute('''
                    UPDATE user_personal_courses 
                    SET title=?, description=?, source=?, course_url=?
                    WHERE id=? AND user_id=?
                ''', (title, description, provider or 'Personal', url or '', course_id, user['id']))
                conn.commit()
                flash('Course updated successfully!', 'success')
                return redirect(url_for('dashboard_my_courses'))
            else:
                flash('Title and description are required.', 'error')
        
        course = conn.execute('''
            SELECT * FROM user_personal_courses 
            WHERE id = ? AND user_id = ?
        ''', (course_id, user['id'])).fetchone()
        
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('dashboard_my_courses'))
        
        return render_template('dashboard/edit_course.html', course=course)
    finally:
        conn.close()

@app.route('/dashboard/delete-course/<int:course_id>', methods=['POST'])
@require_auth
def dashboard_delete_course(course_id):
    """Delete user's course"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    try:
        conn.execute('''
            DELETE FROM user_personal_courses 
            WHERE id = ? AND user_id = ?
        ''', (course_id, user['id']))
        conn.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard_my_courses'))

@app.route('/complete-course/<int:course_id>', methods=['POST'])
@require_login
def complete_course(course_id):
    """Mark a course as completed for the current user"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if already completed
        existing = conn.execute('''
            SELECT * FROM user_courses 
            WHERE user_id = ? AND course_id = ?
        ''', (user['id'], course_id)).fetchone()
        
        if existing and existing['completed']:
            flash('Course already completed!', 'info')
            return redirect(url_for('dashboard'))
        
        # Mark as completed
        if existing:
            # Update existing record
            conn.execute('''
                UPDATE user_courses 
                SET completed = 1, completion_date = datetime('now')
                WHERE user_id = ? AND course_id = ?
            ''', (user['id'], course_id))
        else:
            # Insert new record
            conn.execute('''
                INSERT INTO user_courses (user_id, course_id, completed, completion_date)
                VALUES (?, ?, 1, datetime('now'))
            ''', (user['id'], course_id))
        
        # Award points to user
        course_points = course['points'] if course['points'] else 0
        conn.execute('''
            UPDATE users 
            SET points = points + ? 
            WHERE id = ?
        ''', (course_points, user['id']))
        
        # Update user level based on new points if needed
        new_points = conn.execute('SELECT points FROM users WHERE id = ?', (user['id'],)).fetchone()['points']
        
        # Determine new level based on points
        if new_points >= 500:
            new_level = 'Expert'
        elif new_points >= 250:
            new_level = 'Intermediate'
        elif new_points >= 100:
            new_level = 'Learner'
        else:
            new_level = 'Beginner'
        
        # Update user level
        conn.execute('UPDATE users SET level = ? WHERE id = ?', (new_level, user['id']))
        
        conn.commit()
        
        flash(f'Course completed! You earned {course_points} points.', 'success')
        
    except Exception as e:
        flash(f'Error completing course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/update-completion-date/<int:course_id>', methods=['POST'])
@require_login
def update_completion_date(course_id):
    """Update completion date for a completed course"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    completion_date = request.form.get('completion_date')
    if not completion_date:
        flash('Completion date is required.', 'error')
        return redirect(url_for('my_courses'))
    
    conn = get_db_connection()
    try:
        # Verify user has completed this course
        user_course = conn.execute('''
            SELECT * FROM user_courses 
            WHERE user_id = ? AND course_id = ? AND completed = 1
        ''', (user['id'], course_id)).fetchone()
        
        if not user_course:
            flash('Course not found or not completed.', 'error')
            return redirect(url_for('my_courses'))
        
        # Update completion date
        conn.execute('''
            UPDATE user_courses 
            SET completion_date = ? 
            WHERE user_id = ? AND course_id = ?
        ''', (completion_date, user['id'], course_id))
        conn.commit()
        
        flash('Completion date updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating completion date: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('my_courses'))

@app.route('/export-courses/<course_type>')
@require_login
def export_courses(course_type):
    """Export courses to CSV"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    import csv
    from io import StringIO
    from flask import Response
    
    conn = get_db_connection()
    try:
        if course_type == 'completed':
            # Use only basic columns that definitely exist
            courses = conn.execute('''
                SELECT c.title, c.description, uc.completion_date
                FROM courses c 
                INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
                ORDER BY uc.completion_date DESC
            ''', (user['id'],)).fetchall()
            filename = f'completed_courses_{user["username"]}.csv'
        elif course_type == 'recommended':
            # Use only basic columns that definitely exist
            courses = conn.execute('''
                SELECT c.title, c.description, '' as completion_date
                FROM courses c 
                LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
                WHERE (uc.completed IS NULL OR uc.completed = 0)
                ORDER BY c.created_at DESC
            ''', (user['id'],)).fetchall()
            filename = f'recommended_courses_{user["username"]}.csv'
        else:
            flash('Invalid course type for export.', 'error')
            return redirect(url_for('my_courses'))
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write simplified header
        writer.writerow(['Title', 'Description', 'Completion Date'])
        
        # Write course data
        for course in courses:
            writer.writerow([
                course['title'], course['description'], course.get('completion_date', '')
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    finally:
        conn.close()

# Alias route for learnings_index referenced in templates
@app.route('/learnings-index')
@require_auth
def learnings_index():
    """Alias for learnings route"""
    return redirect(url_for('learnings'))

# Test route to debug template rendering
@app.route('/test-page')
def test_page():
    """Test page for debugging"""
    return render_template('test_page.html')

# Debug route to check session status
@app.route('/debug/session')
def debug_session():
    """Debug route to check current session status"""
    session_token = session.get('session_token')
    user = get_current_user()
    
    debug_info = {
        'has_session_token': bool(session_token),
        'session_token': session_token[:10] + '...' if session_token else None,
        'user_from_g': user,
        'flask_session_keys': list(session.keys()),
        'request_endpoint': request.endpoint
    }
    
    return f"<pre>{debug_info}</pre>"

# Main application entry point
if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
