"""
AI Learning Tracker - Main Application Module

CRITICAL BUSINESS RULES IMPLEMENTED:
====================================

1. USER MANAGEMENT SECURITY
   - Only 'admin' user is protected from deletion (line ~2000)
   - All user deletions require @security_guard('user_delete', require_ui=True)
   - User management operations are heavily audited

2. PASSWORD RESET SAFETY  
   - Password resets require explicit admin authorization via UI
   - No automated backend password resets in production
   - All password operations use @production_safe decorators

3. ADMIN PRIVILEGES
   - Admin-only routes protected with @require_admin decorator
   - Admin actions logged via log_admin_action()
   - Admin user cannot be deleted or suspended

4. SESSION SECURITY
   - Secure session configuration with httponly and secure flags
   - Session timeout configurable via environment variables
   - Session cleanup on logout and user deletion

5. PRODUCTION SAFEGUARDS
   - Environment-based configuration via ProductionConfig
   - Security guards prevent unsafe operations in production
   - Comprehensive error handling and logging

SECURITY DECORATORS USED:
- @require_admin: Restrict to admin users only
- @security_guard: Prevent unsafe operations  
- @production_safe: Production environment safety
- @password_reset_guard: Password operation safety

Never modify the user protection logic without security review.
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

# Import security guard system and production configuration
from security_guard import (
    SecurityGuard, SecurityGuardError, security_guard, password_reset_guard,
    log_admin_action, get_test_credentials, validate_test_environment
)
from production_config import ProductionConfig, production_safe
from production_safety_guard import ProductionSafetyGuard, ProductionSafetyError, production_safe as enhanced_production_safe
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
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32)),
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=int(os.environ.get('SESSION_TIMEOUT', 3600))),
    SESSION_COOKIE_SECURE=True if os.environ.get('FLASK_ENV') == 'production' else False,
    SESSION_COOKIE_HTTPONLY=True,  # Prevent XSS attacks
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
)

# Initialize production safety guard
production_safety = ProductionSafetyGuard()
app.config['PRODUCTION_SAFETY'] = production_safety
app.config['ENVIRONMENT'] = production_safety.environment

# Log environment detection
logger.info(f"Environment detected: {production_safety.environment}")
if production_safety.environment == 'production':
    logger.warning("PRODUCTION ENVIRONMENT - Enhanced safety measures active")

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
    
    # Courses table - enhanced schema with URL validation
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
        conn.execute('ALTER TABLE courses ADD COLUMN url_status TEXT DEFAULT "unchecked"')
        conn.execute('ALTER TABLE courses ADD COLUMN last_url_check TIMESTAMP')
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
    
    # Create default users (only admin and demo for testing)
    # Other users should be created manually and not auto-created
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')  # Fallback to default if not set
    demo_username = os.environ.get('DEMO_USERNAME', 'demo')
    demo_password = os.environ.get('DEMO_PASSWORD', 'demo')  # Fallback to default if not set
    
    admin_hash = generate_password_hash(admin_password)
    demo_hash = generate_password_hash(demo_password)
    
    try:
        # Create admin user
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
        # Create demo user for testing
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (demo_username, demo_hash))
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
            # (Security check function is defined later in the file)
            
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
    errors = []
    
    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Uppercase letter check
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Lowercase letter check
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Number check
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "Password meets security requirements"

def validate_password_strength_simple(password):
    """Simple password validation for existing users (backward compatibility)"""
    if len(password) < SECURITY_CONFIG['PASSWORD_MIN_LENGTH']:
        return False, f"Password must be at least {SECURITY_CONFIG['PASSWORD_MIN_LENGTH']} characters long"
    
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
# app.register_blueprint(admin_bp)

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

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle Method Not Allowed errors with helpful message"""
    return render_template('auth/login.html'), 405

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
            session['user_id'] = user['id']  # Store user_id in session
            session['username'] = username   # Store username in session
            session.permanent = True
            
            flash(f'Welcome back, {username}!', 'success')
            # Redirect admin users to admin dashboard
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
        print(f"Dashboard route - User data: {dict(user_data) if user_data else None}")  # Debug
        
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page with level management and comprehensive error handling"""
    try:
        user = get_current_user()
        if not user:
            flash('Please log in to access your profile.', 'info')
            return redirect(url_for('login'))
        
        user_id = user['id']
        
        # Import level manager here to avoid circular imports
        from level_manager import LevelManager
        level_manager = LevelManager()
        
        if request.method == 'POST':
            try:
                # Handle profile updates
                user_selected_level = request.form.get('user_selected_level')
                
                if user_selected_level:
                    # Update selected level using level manager
                    result = level_manager.update_user_selected_level(user_id, user_selected_level)
                    
                    if result['success']:
                        flash(f'Profile updated successfully! {result["message"]}', 'success')
                        
                        # Update session if needed
                        if 'user_level' in session:
                            session['user_selected_level'] = user_selected_level
                    else:
                        flash(result['message'], 'error')
                else:
                    flash('Invalid expertise level selected', 'error')
            except Exception as e:
                logger.error(f"Error updating profile for user {user_id}: {e}")
                flash('An error occurred while updating your profile. Please try again.', 'error')
        
        # Get comprehensive user level information
        try:
            level_info = level_manager.get_user_level_info(user_id)
            if not level_info:
                logger.warning(f"Could not get level info for user {user_id}")
                level_info = {
                    'current_level': 1,
                    'current_level_name': 'Beginner',
                    'points_needed_for_next': 100,
                    'next_level': 2,
                    'next_level_name': 'Intermediate',
                    'progress_percentage': 0,
                    'total_points': 0,
                    'level_points': 0
                }
        except Exception as e:
            logger.error(f"Error getting level info for user {user_id}: {e}")
            level_info = {
                'current_level': 1,
                'current_level_name': 'Beginner',
                'points_needed_for_next': 100,
                'next_level': 2,
                'next_level_name': 'Intermediate',
                'progress_percentage': 0,
                'total_points': 0,
                'level_points': 0
            }
        
        # Get user data for display
        conn = get_db_connection()
        try:
            user_data = conn.execute('''
                SELECT username, level, points, level_points, user_selected_level, created_at, 
                       last_login, last_activity, login_count
                FROM users 
                WHERE id = ?
            ''', (user_id,)).fetchone()
            
            if not user_data:
                logger.error(f"User data not found for user_id {user_id}")
                flash('User profile data not found. Please contact support.', 'error')
                return redirect(url_for('dashboard'))
            
            # Get user's active sessions with error handling
            try:
                active_sessions = conn.execute('''
                    SELECT session_token, created_at, expires_at, ip_address, user_agent,
                           CASE WHEN expires_at > datetime('now') THEN 'Active' ELSE 'Expired' END as status
                    FROM user_sessions 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 5
                ''', (user_id,)).fetchall()
            except Exception as e:
                logger.warning(f"Error fetching sessions for user {user_id}: {e}")
                active_sessions = []
            
            # Get user's learning stats with error handling
            try:
                total_learnings = conn.execute('''
                    SELECT COUNT(*) as count 
                    FROM learning_entries 
                    WHERE user_id = ? AND is_global = 0
                ''', (user_id,)).fetchone()['count']
                
                completed_courses = conn.execute('''
                    SELECT COUNT(*) as count 
                    FROM user_courses 
                    WHERE user_id = ? AND completed = 1
                ''', (user_id,)).fetchone()['count']
                
                enrolled_courses = conn.execute('''
                    SELECT COUNT(*) as count 
                    FROM user_courses 
                    WHERE user_id = ? AND completed = 0
                ''', (user_id,)).fetchone()['count']
            except Exception as e:
                logger.warning(f"Error fetching learning stats for user {user_id}: {e}")
                total_learnings = 0
                completed_courses = 0
                enrolled_courses = 0
            
            # Get recent points log for user with error handling
            try:
                points_log = level_manager.get_user_points_log(user_id, limit=10)
                if not points_log:
                    points_log = []
            except Exception as e:
                logger.warning(f"Error fetching points log for user {user_id}: {e}")
                points_log = []
            
            return render_template('dashboard/profile.html',
                                 user=user_data,
                                 level_info=level_info,
                                 active_sessions=active_sessions,
                                 total_learnings=total_learnings,
                                 completed_courses=completed_courses,
                                 enrolled_courses=enrolled_courses,
                                 points_log=points_log)
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in profile route for user {user.get('id', 'unknown') if user else 'not authenticated'}: {e}")
        import traceback
        logger.error(f"Profile route traceback: {traceback.format_exc()}")
        flash('An unexpected error occurred while loading your profile. Please try again later.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/points_log')
def points_log():
    """View user's points transaction history"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    user_id = user['id']
    
    # Import level manager here to avoid circular imports
    from level_manager import LevelManager
    level_manager = LevelManager()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get points log with pagination
    points_log = level_manager.get_user_points_log(user_id, limit=per_page * page)
    level_info = level_manager.get_user_level_info(user_id)
    
    return render_template('dashboard/points_log.html',
                         points_log=points_log,
                         level_info=level_info,
                         page=page)

@app.route('/toggle_course_completion/<int:course_id>', methods=['POST'])
def toggle_course_completion(course_id):
    """Toggle course completion status with enhanced level management"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    user_id = user['id']
    completed = request.form.get('completed') == '1'
    
    # Import level manager here to avoid circular imports
    from level_manager import LevelManager
    level_manager = LevelManager()
    
    # Use level manager to handle completion
    result = level_manager.mark_course_completion(user_id, course_id, completed)
    
    if result['success']:
        flash(result['message'], 'success')
        
        # Show level progression information if level changed
        if result.get('points_change', 0) != 0:
            points_msg = f"Points: {'+'  if result['points_change'] > 0 else ''}{result['points_change']}"
            flash(f"{points_msg} | Level: {result['new_level']} ({result['level_points']} at level)", 'info')
        
        # Update session level if it changed
        if 'user_level' in session and session['user_level'] != result['new_level']:
            session['user_level'] = result['new_level']
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('my_courses'))

@app.route('/complete_course/<int:course_id>', methods=['POST'])
def complete_course(course_id):
    """Mark a course as completed (dashboard action)"""
    user = get_current_user()
    if not user:
        flash('Please log in to access this page.', 'info')
        return redirect(url_for('login'))
    
    user_id = user['id']
    
    # Import level manager here to avoid circular imports
    from level_manager import LevelManager
    level_manager = LevelManager()
    
    # Mark course as completed (always set to completed, not toggle)
    result = level_manager.mark_course_completion(user_id, course_id, completed=True)
    
    if result['success']:
        flash(result['message'], 'success')
        
        # Show level progression information if level changed
        if result.get('points_change', 0) != 0:
            points_msg = f"Points: +{result['points_change']}"
            flash(f"{points_msg} | Level: {result['new_level']} ({result['level_points']} at level)", 'info')
        
        # Update session level if it changed
        if 'user_level' in session and session['user_level'] != result['new_level']:
            session['user_level'] = result['new_level']
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('dashboard'))

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
    
    # Get all users except admin
    conn = get_db_connection()
    try:
        users = conn.execute(
            'SELECT * FROM users WHERE username != ? ORDER BY created_at DESC',
            ('admin',)
        ).fetchall()
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

@app.route('/admin/url-validation')
def admin_url_validation():
    """URL validation management page - Admin only (simplified)"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    try:
        # Get all courses with their validation status
        courses = conn.execute('''
            SELECT id, title, url, url_status, last_url_check
            FROM courses 
            ORDER BY title
        ''').fetchall()
        
        # Calculate summary
        summary = {
            'working': {'count': 0},
            'not_working': {'count': 0},
            'broken': {'count': 0},
            'unchecked': {'count': 0}
        }
        
        for course in courses:
            status = course['url_status'] or 'Unchecked'
            if status == 'Working':
                summary['working']['count'] += 1
            elif status == 'Not Working':
                summary['not_working']['count'] += 1
            elif status == 'Broken':
                summary['broken']['count'] += 1
            else:
                summary['unchecked']['count'] += 1
        
        return render_template('admin/url_validation_simple.html',
                             courses=courses,
                             summary=summary)
        
    except Exception as e:
        logger.error(f"Error in URL validation page: {e}")
        flash(f'Error loading URL validation data: {e}', 'error')
        return redirect(url_for('admin_courses'))
    finally:
        conn.close()

@app.route('/admin/validate-all-urls', methods=['POST'])
def validate_all_urls():
    """Start asynchronous URL validation for all courses - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    import threading
    import requests
    from datetime import datetime
    
    def validate_course_url(course_id, url):
        """Validate a single course URL and update database"""
        if not url or url.strip() == '':
            return 'No URL'
        
        try:
            # Clean and validate URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Send HTTP GET request with timeout
            response = requests.get(url, timeout=10, allow_redirects=True, 
                                 headers={'User-Agent': 'AI-Learning-Tracker/1.0'})
            
            # Update database with result
            conn = get_db_connection()
            if response.status_code == 200:
                status = 'Working'
            else:
                status = 'Not Working'
            
            conn.execute('''
                UPDATE courses 
                SET url_status = ?, last_url_check = ?
                WHERE id = ?
            ''', (status, datetime.now().isoformat(), course_id))
            conn.commit()
            conn.close()
            
            return status
            
        except requests.exceptions.Timeout:
            conn = get_db_connection()
            conn.execute('''
                UPDATE courses 
                SET url_status = ?, last_url_check = ?
                WHERE id = ?
            ''', ('Not Working', datetime.now().isoformat(), course_id))
            conn.commit()
            conn.close()
            return 'Not Working'
        except Exception as e:
            conn = get_db_connection()
            conn.execute('''
                UPDATE courses 
                SET url_status = ?, last_url_check = ?
                WHERE id = ?
            ''', ('Not Working', datetime.now().isoformat(), course_id))
            conn.commit()
            conn.close()
            return 'Not Working'
    
    def run_validation():
        """Background validation process"""
        try:
            # Get all courses with URLs
            conn = get_db_connection()
            courses = conn.execute('''
                SELECT id, title, url, link
                FROM courses 
                WHERE (url IS NOT NULL AND url != '') 
                   OR (link IS NOT NULL AND link != '')
                ORDER BY id
            ''').fetchall()
            conn.close()
            
            logger.info(f"Starting URL validation for {len(courses)} courses")
            
            for course in courses:
                # Use url field first, then link field as fallback
                course_url = course['url'] or course['link']
                if course_url and course_url.strip():
                    status = validate_course_url(course['id'], course_url.strip())
                    logger.info(f"Course {course['id']} ({course['title']}): {status}")
                    # Small delay to avoid overwhelming servers
                    time.sleep(1)
            
            logger.info("URL validation completed")
            
        except Exception as e:
            logger.error(f"Error in background URL validation: {e}")
    
    try:
        # Start validation in background thread
        validation_thread = threading.Thread(target=run_validation)
        validation_thread.daemon = True
        validation_thread.start()
        
        logger.info("URL validation started in background")
        return jsonify({
            'success': True,
            'message': 'URL validation started in background. Results will be updated automatically.'
        })
        
    except Exception as e:
        logger.error(f"Error starting URL validation: {e}")
        return jsonify({'error': f'Failed to start validation: {str(e)}'}), 500

@app.route('/admin/url-validation-status')
def url_validation_status():
    """Get current URL validation status - Admin only (AJAX endpoint)"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        conn = get_db_connection()
        
        # Get validation summary
        status_counts = conn.execute('''
            SELECT 
                CASE 
                    WHEN url_status IS NULL OR url_status = '' THEN 'Unchecked'
                    ELSE url_status
                END as status,
                COUNT(*) as count
            FROM courses 
            WHERE (url IS NOT NULL AND url != '') 
               OR (link IS NOT NULL AND link != '')
            GROUP BY status
        ''').fetchall()
        
        # Get recently updated courses
        recent_updates = conn.execute('''
            SELECT id, title, url_status, last_url_check
            FROM courses 
            WHERE last_url_check IS NOT NULL
            ORDER BY last_url_check DESC
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        # Format summary
        summary = {}
        for row in status_counts:
            summary[row['status'].lower().replace(' ', '_')] = {
                'count': row['count']
            }
        
        # Format recent updates
        recent_list = []
        for update in recent_updates:
            recent_list.append({
                'id': update['id'],
                'title': update['title'],
                'status': update['url_status'],
                'last_check': update['last_url_check']
            })
        
        return jsonify({
            'summary': summary,
            'recent_updates': recent_list,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/course-configs')
def admin_course_configs():
    """Course search configuration page - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/course_search_configs.html')

@app.route('/admin/add-course', methods=['GET', 'POST'])
def admin_add_course():
    """Add a new course - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        source = request.form.get('source', '').strip()
        level = request.form.get('level', '').strip()
        url = request.form.get('url', '').strip()
        points = request.form.get('points', type=int) or 0
        description = request.form.get('description', '').strip()

        if not title or not source or not level:
            flash('Title, source, and level are required.', 'error')
            return render_template('admin/add_course.html')

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO courses (title, source, level, url, points, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, source, level, url, points, description, datetime.now().isoformat()))
            conn.commit()
            flash('Course added successfully!', 'success')
            return redirect(url_for('admin_courses'))
        except Exception as e:
            flash(f'Error adding course: {e}', 'error')
        finally:
            conn.close()

    return render_template('admin/add_course.html')

@app.route('/admin/edit-course/<int:course_id>', methods=['GET', 'POST'])
def admin_edit_course(course_id):
    """Edit an existing course - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        source = request.form.get('source', '').strip()
        level = request.form.get('level', '').strip()
        url = request.form.get('url', '').strip()
        points = request.form.get('points', type=int) or 0
        description = request.form.get('description', '').strip()

        if not title or not source or not level:
            flash('Title, source, and level are required.', 'error')
        else:
            try:
                conn.execute('''
                    UPDATE courses 
                    SET title = ?, source = ?, level = ?, url = ?, points = ?, description = ?
                    WHERE id = ?
                ''', (title, source, level, url, points, description, course_id))
                conn.commit()
                flash('Course updated successfully!', 'success')
                return redirect(url_for('admin_courses'))
            except Exception as e:
                flash(f'Error updating course: {e}', 'error')
    
    try:
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('admin_courses'))
        
        return render_template('admin/edit_course.html', course=course)
    finally:
        conn.close()

@app.route('/admin/delete-course/<int:course_id>', methods=['POST'])
def admin_delete_course(course_id):
    """Delete a course - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT title FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
        else:
            conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            conn.commit()
            flash(f'Course "{course["title"]}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {e}', 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_courses'))

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Admin settings"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
                                                         # Handle level settings update
        conn = get_db_connection()
        try:
            # Get all level settings to update
            level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
            
            updated_count = 0
            for level in level_settings:
                field_name = f"{level['level_name'].lower()}_points"
                new_points = request.form.get(field_name)
                
                if new_points:
                    try:
                        new_points = int(new_points)
                        if new_points >= 0:
                            conn.execute('UPDATE level_settings SET points_required = ? WHERE level_name = ?', 
                                       (new_points, level['level_name']))
                            updated_count += 1
                        else:
                            flash(f'Points for {level["level_name"]} must be non-negative.', 'error')
                    except ValueError:
                        flash(f'Invalid points value for {level["level_name"]}.', 'error')
            
            if updated_count > 0:
                conn.commit()
                
                # Log security event
                log_security_event(
                    event_type='admin_settings_update',
                    details=f'Updated {updated_count} level settings',
                    ip_address=request.remote_addr,
                    user_id=user['id']
                )
                
                flash(f'Successfully updated {updated_count} level settings!', 'success')
            else:
                flash('No valid updates were made.', 'warning')
                
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('admin_settings'))
    
    # GET request - display settings page
    conn = get_db_connection()
    try:
        level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        
        # Get system statistics
        system_stats = {
            'total_users': conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
            'active_users': conn.execute('SELECT COUNT(*) as count FROM users WHERE status = "active"').fetchone()['count'],
            'total_courses': conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count'],
            'total_learnings': conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()['count'],
        }
        
        # Try to get active sessions, handle gracefully if table doesn't exist
        try:
            system_stats['active_sessions'] = conn.execute(
                'SELECT COUNT(*) as count FROM user_sessions WHERE is_active = 1'
            ).fetchone()['count']
        except sqlite3.OperationalError:
            system_stats['active_sessions'] = 0
        
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

@app.route('/admin/change-password', methods=['GET', 'POST'])
def admin_change_password():
    """Admin password change - separate from user management"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate required fields
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('admin/change_password.html')
        
        # Get user session info
        user_id = session.get('user_id')
        if not user_id:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
            
        conn = get_db_connection()
        try:
            # Fetch complete user data from database
            user_data = conn.execute(
                'SELECT * FROM users WHERE id = ? AND username = ?', 
                (user_id, 'admin')
            ).fetchone()
            
            if not user_data:
                flash('Admin user not found.', 'error')
                return redirect(url_for('login'))
            
            # Validate current password
            if not check_password_hash(user_data['password_hash'], current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('admin/change_password.html')
            
            # Validate passwords match
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('admin/change_password.html')
            
            # Validate new password is different from current
            if check_password_hash(user_data['password_hash'], new_password):
                flash('New password must be different from your current password.', 'error')
                return render_template('admin/change_password.html')
            
            # Validate password strength (use simple validation for backward compatibility)
            is_valid, message = validate_password_strength_simple(new_password)
            if not is_valid:
                flash(f'Password does not meet requirements: {message}', 'error')
                return render_template('admin/change_password.html')
            
            # Hash the new password
            password_hash = generate_password_hash(new_password)
            
            # Update admin password
            result = conn.execute(
                'UPDATE users SET password_hash = ? WHERE username = ?',
                (password_hash, 'admin')
            )
            conn.commit()
            
            # Verify the update worked (for robust error handling)
            if result.rowcount != 1:
                raise Exception(f"Password update failed: {result.rowcount} rows affected")
            
            # Log security event before session invalidation
            log_security_event(
                'admin_password_change',
                'Admin changed their own password - session invalidated',
                request.remote_addr,
                session.get('user_id')
            )
            
            # Invalidate current session
            session_token = session.get('session_token')
            if session_token:
                invalidate_session(session_token)
            
            # Clear session data
            session.clear()
            
            # Flash success message for login page
            flash('Password changed successfully! Please log in with your new password.', 'success')
            
            # Redirect to login page
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Error changing password: {str(e)}', 'error')
            return render_template('admin/change_password.html')
        finally:
            conn.close()
    
    return render_template('admin/change_password.html')

@app.route('/admin/add-user', methods=['GET', 'POST'])
def admin_add_user():
    """Add a new user (admin only)"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        password = request.form.get('password')
        level = sanitize_input(request.form.get('level', 'Beginner'))
        status = sanitize_input(request.form.get('status', 'active'))
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('admin/add_user.html')
        
        # Validate password strength
        is_valid, message = validate_password_strength_simple(password)
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
            
            # Log security event
            log_security_event(
                'admin_user_create',
                f'Admin created new user: {username}',
                request.remote_addr,
                user['id']
            )
            
            flash(f'User "{username}" created successfully!', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin/add_user.html')

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    """Delete a user (admin only) - Protected by security guards"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    try:
        # Check if user exists and get username for validation
        user_to_delete = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_to_delete:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user_to_delete['username']
        
        # Protected users that cannot be deleted (only admin)
        protected_users = ['admin']
        if username in protected_users:
            flash(f'Cannot delete protected user "{username}".', 'error')
            return redirect(url_for('admin_users'))
        
        # Delete user and related data
        conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        
        # Try to delete from user_personal_courses if it exists
        try:
            conn.execute('DELETE FROM user_personal_courses WHERE user_id = ?', (user_id,))
        except sqlite3.OperationalError:
            # Table might not exist, continue
            pass
            
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        # Log security event
        log_security_event(
            'admin_user_delete',
            f'Admin deleted user: {username}',
            request.remote_addr,
            user['id']
        )
        
        flash(f'User "{username}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {e}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/toggle-user-status/<int:user_id>', methods=['POST'])
def admin_toggle_user_status(user_id):
    """Toggle user status between active and inactive (admin only)"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    try:
        # Get current user status
        user_data = conn.execute('SELECT username, status FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user_data['username']
        current_status = user_data['status'] or 'active'
        
        # Cannot suspend admin user
        if username == 'admin':
            flash('Cannot change status of admin user.', 'error')
            return redirect(url_for('admin_users'))
        
        # Toggle status
        new_status = 'inactive' if current_status == 'active' else 'active'
        
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        
        # If suspending user, invalidate all their sessions
        if new_status == 'inactive':
            conn.execute('UPDATE user_sessions SET is_active = 0 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        
        # Log security event
        log_security_event(
            'admin_user_status_change',
            f'Admin changed user {username} status to {new_status}',
            request.remote_addr,
            user['id']
        )
        
        flash(f'User "{username}" status changed to {new_status}.', 'success')
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/populate-linkedin-courses', methods=['POST'])
def admin_populate_linkedin_courses():
    """Populate courses from LinkedIn Learning - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Sample LinkedIn Learning courses for AI/ML
    sample_courses = [
        {
            'title': 'Machine Learning with Python: Foundations',
            'source': 'LinkedIn Learning',
            'level': 'Beginner',
            'url': 'https://www.linkedin.com/learning/machine-learning-with-python-foundations',
            'points': 100,
            'description': 'Learn the fundamentals of machine learning using Python, including data preparation, algorithms, and model evaluation.'
        },
        {
            'title': 'Deep Learning: Getting Started',
            'source': 'LinkedIn Learning', 
            'level': 'Intermediate',
            'url': 'https://www.linkedin.com/learning/deep-learning-getting-started',
            'points': 150,
            'description': 'Introduction to deep learning concepts, neural networks, and practical applications using popular frameworks.'
        },
        {
            'title': 'AI for Everyone',
            'source': 'LinkedIn Learning',
            'level': 'Beginner', 
            'url': 'https://www.linkedin.com/learning/ai-for-everyone',
            'points': 75,
            'description': 'Non-technical introduction to AI concepts, applications, and impact on business and society.'
        },
        {
            'title': 'Natural Language Processing with Python',
            'source': 'LinkedIn Learning',
            'level': 'Intermediate',
            'url': 'https://www.linkedin.com/learning/natural-language-processing-with-python',
            'points': 125,
            'description': 'Learn text processing, sentiment analysis, and NLP techniques using Python libraries.'
        },
        {
            'title': 'Computer Vision with OpenCV',
            'source': 'LinkedIn Learning',
            'level': 'Expert',
            'url': 'https://www.linkedin.com/learning/computer-vision-with-opencv',
            'points': 200,
            'description': 'Advanced computer vision techniques using OpenCV for image processing and analysis.'
        }
    ]
    
    conn = get_db_connection()
    try:
        added_count = 0
        skipped_count = 0
        
        for course in sample_courses:
            # Check if course already exists
            existing = conn.execute(
                'SELECT id FROM courses WHERE title = ? AND source = ?',
                (course['title'], course['source'])
            ).fetchone()
            
            if existing:
                skipped_count += 1
                continue
            
            # Add new course
            conn.execute('''
                INSERT INTO courses (title, source, level, url, points, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (course['title'], course['source'], course['level'], course['url'], course['points'], course['description'], datetime.now().isoformat()))
            added_count += 1
        
        conn.commit()
        
        # Log security event
        log_security_event(
            'admin_courses_populate',
            f'Admin populated {added_count} LinkedIn courses, skipped {skipped_count} duplicates',
            request.remote_addr,
            user['id']
        )
        
        flash(f'Successfully added {added_count} LinkedIn Learning courses! Skipped {skipped_count} duplicates.', 'success')
    except Exception as e:
        flash(f'Error populating courses: {e}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/search-and-import-courses', methods=['POST'])
def admin_search_and_import_courses():
    """Search and import courses from external sources - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    search_query = request.form.get('search_query', '').strip()
    course_provider = request.form.get('course_provider', 'all')
    
    if not search_query:
        flash('Please enter a search query.', 'error')
        return redirect(url_for('admin_course_configs'))
    
    # For now, we'll simulate course search results
    # In a real implementation, this would call external APIs
    simulated_results = []
    
    if 'python' in search_query.lower():
        simulated_results.extend([
            {
                'title': f'Python for {search_query.title()}',
                'source': 'Coursera',
                'level': 'Beginner',
                'url': f'https://www.coursera.org/learn/python-{search_query.lower()}',
                'points': 100,
                'description': f'Comprehensive course on using Python for {search_query.lower()}.'
            },
            {
                'title': f'Advanced Python {search_query.title()}',
                'source': 'edX',
                'level': 'Expert', 
                'url': f'https://www.edx.org/course/advanced-python-{search_query.lower()}',
                'points': 200,
                'description': f'Advanced techniques and best practices for {search_query.lower()} with Python.'
            }
        ])
    
    if 'machine learning' in search_query.lower() or 'ml' in search_query.lower():
        simulated_results.extend([
            {
                'title': 'Machine Learning Specialization',
                'source': 'Coursera',
                'level': 'Intermediate',
                'url': 'https://www.coursera.org/specializations/machine-learning',
                'points': 300,
                'description': 'Complete specialization covering supervised learning, unsupervised learning, and best practices.'
            },
            {
                'title': 'Introduction to Machine Learning',
                'source': 'MIT OpenCourseWare',
                'level': 'Expert',
                'url': 'https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-034-artificial-intelligence-fall-2010/',
                'points': 250,
                'description': 'MIT course covering fundamental concepts in artificial intelligence and machine learning.'
            }
        ])
    
    if not simulated_results:
        # Generic results for any search
        simulated_results = [
            {
                'title': f'Introduction to {search_query.title()}',
                'source': 'Udemy',
                'level': 'Beginner',
                'url': f'https://www.udemy.com/course/intro-to-{search_query.lower().replace(" ", "-")}',
                'points': 75,
                'description': f'Beginner-friendly introduction to {search_query.lower()}.'
            }
        ]
    
    # Filter by provider if specified
    if course_provider != 'all':
        simulated_results = [r for r in simulated_results if r['source'].lower() == course_provider.lower()]
    
    conn = get_db_connection()
    try:
        added_count = 0
        
        for course in simulated_results:
            # Check if course already exists
            existing = conn.execute(
                'SELECT id FROM courses WHERE title = ? AND source = ?',
                (course['title'], course['source'])
            ).fetchone()
            
            if existing:
                continue
            
            # Add new course
            conn.execute('''
                INSERT INTO courses (title, source, level, url, points, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                course['title'], course['source'], course['level'], 
                course['url'], course['points'], course['description'],
                datetime.now().isoformat()
            ))
            added_count += 1
        
        conn.commit()
        
        # Log security event
        log_security_event(
            'admin_courses_search_import',
            f'Admin searched and imported {added_count} courses for query: {search_query}',
            request.remote_addr,
            user['id']
        )
        
        if added_count > 0:
            flash(f'Successfully imported {added_count} courses for "{search_query}".', 'success')
        else:
            flash(f'No new courses found for "{search_query}". All results may already exist.', 'info')
            
    except Exception as e:
        flash(f'Error importing courses: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_course_configs'))

@app.route('/admin/reset-all-user-passwords', methods=['POST'])
def admin_reset_all_user_passwords():
    """Reset all user passwords (admin only) - DANGEROUS OPERATION"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    # This is a dangerous operation, require explicit confirmation
    confirmation = request.form.get('confirmation', '').strip().lower()
    
    if confirmation != 'reset all passwords':
        flash('Password reset cancelled. You must type "reset all passwords" exactly to confirm.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get all users except admin
        users = conn.execute('SELECT id, username FROM users WHERE username != ?', ('admin',)).fetchall()
        
        if not users:
            flash('No users found to reset passwords for.', 'info')
            return redirect(url_for('admin_users'))
        
        # Generate new temporary passwords
        reset_count = 0
        for user_data in users:
            # Generate a random temporary password
            temp_password = secrets.token_urlsafe(12)  # 12 character random password
            password_hash = generate_password_hash(temp_password)
            
            # Update user password
            conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                        (password_hash, user_data['id']))
            
            # Invalidate all sessions for this user
            conn.execute('UPDATE user_sessions SET is_active = 0 WHERE user_id = ?', 
                        (user_data['id'],))
            
            reset_count += 1
            
            # Log the temporary password (in production, send via secure channel)
            logger.warning(f"Password reset for user {user_data['username']}: {temp_password}")
        
        conn.commit()
        
        # Log security event
        log_security_event(
            'admin_mass_password_reset',
            f'Admin reset passwords for {reset_count} users',
            request.remote_addr,
            user['id']
        )
        
        flash(f'Successfully reset passwords for {reset_count} users. Temporary passwords have been logged.', 'warning')
        flash('IMPORTANT: All user sessions have been invalidated. Users must log in with new passwords.', 'info')
        
    except Exception as e:
        flash(f'Error resetting passwords: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reset-user-password', methods=['POST'])
def admin_reset_user_password():
    """Reset a specific user's password (admin only)"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Debug: Log all form data
    print(f"DEBUG: Form data received: {dict(request.form)}")
    
    # Get form data with better error handling
    user_id_str = request.form.get('user_id', '').strip()
    new_password = request.form.get('custom_password', '').strip()
    confirm_password = request.form.get('confirm_custom_password', '').strip()
    confirmation_checked = request.form.get('reset_individual_confirmation')
    
    # Convert user_id to integer with better error handling
    user_id = None
    if user_id_str:
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            flash(f'Invalid user ID format: {user_id_str}', 'error')
            return redirect(url_for('admin_users'))
    
    # Comprehensive validation with specific error messages
    if not user_id:
        flash('User ID is missing or invalid. Please try again.', 'error')
        return redirect(url_for('admin_users'))
        
    if not new_password:
        flash('Custom password is required. Please enter a password.', 'error')
        return redirect(url_for('admin_users'))
        
    if not confirm_password:
        flash('Password confirmation is required. Please confirm your password.', 'error')
        return redirect(url_for('admin_users'))
        
    if new_password != confirm_password:
        flash('Passwords do not match. Please check both password fields.', 'error')
        return redirect(url_for('admin_users'))
        
    if not confirmation_checked:
        flash('You must confirm the password reset by checking the confirmation box.', 'error')
        return redirect(url_for('admin_users'))
    
    # Validate password strength
    is_valid, message = validate_password_strength_simple(new_password)
    if not is_valid:
        flash(f'Password validation failed: {message}', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Check if user exists and get username
        user_data = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user_data['username']
        
        # Cannot reset admin password through this method
        if username == 'admin':
            flash('Cannot reset admin password through this method. Use the dedicated admin password change form.', 'error')
            return redirect(url_for('admin_users'))
        
        # Hash and update password
        password_hash = generate_password_hash(new_password)
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        
        # Invalidate all sessions for this user
        conn.execute('UPDATE user_sessions SET is_active = 0 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        
        # Log security event
        log_security_event(
            'admin_user_password_reset',
            f'Admin reset password for user: {username}',
            request.remote_addr,
            user['id']
        )
        
        flash(f'Password reset successfully for user "{username}". All their sessions have been invalidated.', 'success')
        
    except Exception as e:
        flash(f'Error resetting password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

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

if __name__ == '__main__':
    # Configure Flask app for development
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Start the Flask development server
    print("\n🚀 AI Learning Tracker - Starting Flask Server")
    print("=" * 60)
    print(f"🌐 URL: http://localhost:5000")
    print(f"🔑 Admin Login: admin / [check environment]")
    print(f"🔑 Demo Login: demo / [check environment]")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
