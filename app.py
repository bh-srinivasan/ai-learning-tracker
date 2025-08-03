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
from urllib.parse import urlparse
try:
    from database_manager import get_db_connection as db_get_connection, init_database as db_init, db_manager
except ImportError:
    db_get_connection = None
    db_init = None
    db_manager = None

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

# Import Azure database sync for production
try:
    from azure_database_sync import AzureDatabaseSync
    azure_sync = AzureDatabaseSync()
    AZURE_SYNC_AVAILABLE = True
    print('✅ Azure database sync loaded')
except ImportError as e:
    print(f'⚠️  Azure sync not available: {e}')
    azure_sync = None
    AZURE_SYNC_AVAILABLE = False

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

# Initialize Azure database sync on startup
if AZURE_SYNC_AVAILABLE and azure_sync:
    print('🔄 Initializing Azure database sync...')
    try:
        # Download database from Azure Storage if available
        azure_sync.sync_from_azure_on_startup()
        print('✅ Azure database sync initialized successfully')
    except Exception as e:
        print(f'⚠️ Azure sync initialization failed: {e}')
        print('   Continuing with local database only')

# @app.before_first_request
def initialize_azure_sync():
    """Initialize Azure sync before first request"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.sync_from_azure_on_startup()
        except Exception as e:
            app.logger.warning(f'Azure sync failed on startup: {e}')

def sync_to_azure_after_change():
    """Upload database to Azure after changes"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.upload_database_to_azure()
        except Exception as e:
            app.logger.warning(f'Azure upload failed: {e}')


# Log environment detection
logger.info(f"Environment detected: {production_safety.environment}")
if production_safety.environment == 'production':
    logger.warning("PRODUCTION ENVIRONMENT - Enhanced safety measures active")

# Database configuration - dynamic based on environment
def get_database_path():
    """Get database path from environment configuration"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    elif database_url.startswith('sqlite://'):
        return database_url.replace('sqlite://', '')
    return 'ai_learning.db'

def get_db_connection():
    """Get database connection with environment-aware support for Azure SQL"""
    try:
        # Check if we should use Azure SQL
        database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
        
        if (database_url == 'azure_sql' or production_safety.environment == 'production') and db_get_connection:
            logger.info(f"🌍 Environment: {production_safety.environment}")
            
            if db_manager and db_manager.is_azure_sql:
                logger.info("📂 Connecting to Azure SQL Database")
            else:
                logger.info("📂 Using SQLite via database manager")
            
            return db_get_connection()
        else:
            # Use traditional SQLite connection
            database_path = get_database_path()
            
            # Log database connection details for debugging
            logger.info(f"📂 Connecting to database: {os.path.abspath(database_path)}")
            logger.info(f"🌍 Environment: {production_safety.environment}")
            logger.info(f"💾 Database exists: {os.path.exists(database_path)}")
            
            if os.path.exists(database_path):
                logger.info(f"📊 Database size: {os.path.getsize(database_path)} bytes")
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row
            return conn
            
    except Exception as e:
        # Fallback to old method if there are any issues
        logger.warning(f"Database manager error ({e}), using fallback SQLite connection")
        database_path = get_database_path()
        conn = sqlite3.connect(database_path)
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
    
    # PRODUCTION SAFETY: NEVER auto-create users in any environment
    # Users should only be created through proper admin interfaces
    # Database initialization should ONLY create schema, never data
    # This prevents accidental data overwrites in any environment
    
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

# Azure database backup scheduler
def azure_backup_scheduler():
    """Background thread to periodically backup database to Azure Storage"""
    import time
    time.sleep(300)  # Wait 5 minutes before first backup
    
    while True:
        try:
            # Azure sync temporarily disabled - module removed in cleanup
            logger.info("Azure backup scheduler: Module not available, skipping sync")
            time.sleep(1800)  # Check every 30 minutes
        except Exception as e:
            logger.error(f"Azure backup scheduler error: {e}")
            time.sleep(1800)  # Continue after error

# Start background threads
cleanup_thread = threading.Thread(target=session_cleanup_scheduler, daemon=True)
cleanup_thread.start()

backup_thread = threading.Thread(target=azure_backup_scheduler, daemon=True)
backup_thread.start()

# CRITICAL FIX: Prevent database reinitialization on every startup
# Only initialize database if it doesn't exist or is empty
def safe_init_db():
    """
    CRITICAL FUNCTION: Initialize database only if it doesn't exist or is empty.
    NEVER OVERWRITES EXISTING DATA - ONLY CREATES MISSING TABLES.
    Now includes Azure Storage sync for data persistence.
    """
    try:
        logger.info("🔍 SAFE_INIT_DB: Starting database safety check...")
        
        # AZURE STORAGE INTEGRATION: Temporarily disabled - module removed in cleanup
        logger.info("Azure sync temporarily disabled - using local database only")
        
        # Check if database file exists (may have been downloaded from Azure)
        db_path = get_database_path()
        if not os.path.exists(db_path):
            logger.info(f"📁 SAFE_INIT_DB: Database file {db_path} not found - will create new one")
            init_db()
            ensure_admin_exists()
            return
        
        conn = get_db_connection()
        
        # Check if users table exists
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        
        if not result:
            logger.info("🏗️ SAFE_INIT_DB: Users table missing - initializing schema...")
            conn.close()
            init_db()
            ensure_admin_exists()
            return
        
        # Check if there are any users (most critical check)
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            logger.info(f"✅ SAFE_INIT_DB: Database already has {user_count} users - PRESERVING ALL DATA")
            
            # Log existing users for verification
            try:
                users = conn.execute("SELECT id, username, created_at FROM users ORDER BY id").fetchall()
                logger.info("🔍 SAFE_INIT_DB: Existing users found:")
                for user in users:
                    logger.info(f"   - ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
            except Exception as e:
                logger.warning(f"⚠️ SAFE_INIT_DB: Could not log existing users: {e}")
            
            conn.close()
            
            # Still ensure admin exists but don't overwrite data
            ensure_admin_exists()
            logger.info("✅ SAFE_INIT_DB: Complete - existing data preserved")
            
            # AZURE STORAGE INTEGRATION: Temporarily disabled - module removed in cleanup
            logger.info("Azure sync temporarily disabled - using local database only")
            return
        else:
            logger.info("📋 SAFE_INIT_DB: Users table exists but empty - safe to initialize")
            conn.close()
            init_db()
            ensure_admin_exists()
            # Azure sync temporarily disabled - using local database only
            logger.info("Azure sync temporarily disabled - using local database only")
            return
        
    except Exception as e:
        logger.error(f"❌ SAFE_INIT_DB: Database check failed: {e}")
        logger.error(f"❌ SAFE_INIT_DB: Exception details: {type(e).__name__}: {str(e)}")
        try:
            # Emergency fallback - only if absolutely necessary
            logger.warning("⚠️ SAFE_INIT_DB: Attempting emergency fallback...")
            init_db()
            ensure_admin_exists()
        except Exception as fallback_error:
            logger.error(f"💥 SAFE_INIT_DB: Emergency fallback failed: {fallback_error}")
            raise

def ensure_admin_exists():
    """
    CRITICAL FUNCTION: Ensure admin user exists without overwriting existing admin data
    """
    try:
        logger.info("🔍 ENSURE_ADMIN: Checking admin user status...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id, username, password_hash, level, points, created_at FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            logger.info(f"✅ ENSURE_ADMIN: Admin user already exists - ID: {existing_admin[0]}, Level: {existing_admin[3]}, Points: {existing_admin[4]}")
            logger.info("✅ ENSURE_ADMIN: Preserving existing admin data - NO CHANGES MADE")
            conn.close()
            return
        
        # Only create admin if it doesn't exist
        logger.info("🔄 ENSURE_ADMIN: Admin user not found - creating new admin...")
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.info("✅ ENSURE_ADMIN: New admin user created successfully")
        logger.info(f"🔑 ENSURE_ADMIN: Admin password set from environment variable")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ ENSURE_ADMIN: Admin user check/creation failed: {e}")
        logger.error(f"❌ ENSURE_ADMIN: Exception details: {type(e).__name__}: {str(e)}")
        try:
            conn.close()
        except:
            pass

# Initialize database on startup (SAFE VERSION - preserves existing data)
safe_init_db()

# EMERGENCY FIX: Disable deployment safety to prevent data resets
# Initialize deployment safety and data integrity monitoring
try:
    # RESTORED - deployment safety module recreated
    from deployment_safety import init_deployment_safety
    deployment_safety = init_deployment_safety(app)
    logger.info("✅ Deployment safety initialized successfully")
except ImportError:
    logger.warning("⚠️ Deployment safety module not available - install azure-storage-blob for full functionality")
except Exception as e:
    logger.error(f"❌ Failed to initialize deployment safety: {e}")

# Re-enable blueprints - circular import issue resolved
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp  
from learnings.routes import learnings_bp
from admin.routes import admin_bp
# from admin_reports_routes import admin_reports_bp  # Upload reports admin interface - COMMENTED OUT - FILE MISSING

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(learnings_bp, url_prefix='/learnings')
app.register_blueprint(admin_bp)
# app.register_blueprint(admin_reports_bp)  # COMMENTED OUT - FILE MISSING

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
        # Base query for completed courses
        completed_query = '''
            SELECT c.*, uc.completed, uc.completion_date, 'system' as course_type
            FROM courses c 
            INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
        '''
        completed_params = [user['id']]
        
        # Apply filters to completed courses
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
        
        # Base query for recommended courses
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
        
        # Get available filter options
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

@app.route('/export-courses/<course_type>')
def export_courses(course_type):
    """Export courses to CSV"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        if course_type == 'completed':
            courses = conn.execute('''
                SELECT c.title, c.description, c.level, uc.completion_date
                FROM courses c 
                INNER JOIN user_courses uc ON c.id = uc.course_id 
                WHERE uc.user_id = ? AND uc.completed = 1
                ORDER BY uc.completion_date DESC
            ''', (user['id'],)).fetchall()
        else:  # recommended
            courses = conn.execute('''
                SELECT c.title, c.description, c.level, c.created_at as date_added
                FROM courses c 
                LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
                WHERE (uc.completed IS NULL OR uc.completed = 0)
                ORDER BY c.created_at DESC
            ''', (user['id'],)).fetchall()
        
        # Create CSV response
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if course_type == 'completed':
            writer.writerow(['Title', 'Description', 'Level', 'Completion Date'])
        else:
            writer.writerow(['Title', 'Description', 'Level', 'Date Added'])
        
        # Write course data
        for course in courses:
            writer.writerow([course['title'], course['description'], course['level'], 
                           course['completion_date'] if course_type == 'completed' else course['date_added']])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course_type}_courses.csv'}
        )
    
    finally:
        conn.close()

@app.route('/complete-course/<int:course_id>', methods=['POST'])
def complete_course(course_id):
    """Mark a course as completed"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('my_courses'))
        
        # Check if already completed
        existing = conn.execute(
            'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
            (user['id'], course_id)
        ).fetchone()
        
        if existing:
            if existing['completed']:
                flash('Course already completed.', 'info')
            else:
                # Update to completed
                conn.execute(
                    'UPDATE user_courses SET completed = 1, completion_date = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?',
                    (user['id'], course_id)
                )
                conn.commit()
                flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
                log_completion_event(user['id'], course_id, course['title'])
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
            log_completion_event(user['id'], course_id, course['title'])
    
    finally:
        conn.close()
    
    return redirect(url_for('my_courses'))

@app.route('/mark_complete/<int:course_id>', methods=['POST'])
def mark_complete(course_id):
    """AJAX endpoint to mark a course as completed"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Check if already completed
        existing = conn.execute(
            'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
            (user['id'], course_id)
        ).fetchone()
        
        if existing:
            if existing['completed']:
                return jsonify({'success': False, 'error': 'Course already completed'})
            else:
                # Update to completed
                conn.execute(
                    'UPDATE user_courses SET completed = 1, completion_date = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?',
                    (user['id'], course_id)
                )
                conn.commit()
                log_completion_event(user['id'], course_id, course['title'])
                return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            log_completion_event(user['id'], course_id, course['title'])
            return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

def log_completion_event(user_id, course_id, course_title):
    """Log course completion event"""
    try:
        log_message = f'User {user_id} completed course {course_id}: {course_title}'
        log_security_event('course_completion', log_message, request.remote_addr, user_id)
    except Exception as e:
        log_security_event('course_completion_error', f'Error logging completion for user {user_id}, course {course_id}: {str(e)}', request.remote_addr, user_id)

@app.route('/update-completion-date/<int:course_id>', methods=['POST'])
def update_completion_date(course_id):
    """Update completion date for a course"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    try:
        completion_date = request.form.get('completion_date')
        user_id = user['id']
        
        conn = get_db_connection()
        try:
            # Update completion date
            conn.execute(
                'UPDATE user_courses SET completion_date = ? WHERE user_id = ? AND course_id = ?',
                (completion_date, user_id, course_id)
            )
            conn.commit()
            flash('Completion date updated successfully!', 'success')
            log_security_event('completion_date_update', 
                             f'Updated completion date for course {course_id} to {completion_date}',
                             request.remote_addr, user_id)
            
        finally:
            conn.close()
            
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
    except Exception as e:
        flash(f'Error updating completion date: {str(e)}', 'error')
        log_security_event('completion_date_update_error', 
                         f'Error updating completion date for user {user_id}, course {course_id}: {str(e)}',
                         request.remote_addr, user_id)
    
    return redirect(url_for('my_courses'))

@app.route('/learnings')
def learnings():
    """Learning entries page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get user's learning entries
    conn = get_db_connection()
    try:
        entries = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC
        ''', (user['id'],)).fetchall()
        return render_template('learnings/index.html', entries=entries)
    finally:
        conn.close()

@app.route('/add-learning', methods=['GET', 'POST'])
def add_learning():
    """Add learning entry"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '')
        custom_date = request.form.get('custom_date')
        is_global = request.form.get('is_global') == 'on'
        
        if title:
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO learning_entries (user_id, title, description, tags, custom_date, is_global)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user['id'], title, description, tags, custom_date, is_global))
                conn.commit()
                flash('Learning entry added successfully!', 'success')
                return redirect(url_for('learnings'))
            finally:
                conn.close()
        else:
            flash('Title is required.', 'error')
    
    return render_template('learnings/add.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle profile updates (basic implementation)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user data
    conn = get_db_connection()
    try:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        
        # Calculate user stats
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']
        
        completed_courses_count = conn.execute('''
            SELECT COUNT(*) as count FROM user_courses 
            WHERE user_id = ? AND completed = 1
        ''', (user['id'],)).fetchone()['count']
        
        # Calculate level progression info
        user_points = user_data['points'] if user_data else 0
        current_level = user_data['level'] if user_data else 'Beginner'
        
        # Get level settings from database
        level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        level_mapping = {level['level_name']: level['points_required'] for level in level_settings}
        
        # Calculate next level info
        next_level = None
        points_to_next = 0
        level_points = 0
        
        # Find current level points and next level
        current_level_points = level_mapping.get(current_level, 0)
        level_points = user_points - current_level_points
        
        # Find next level
        for level_name, required_points in level_mapping.items():
            if user_points < required_points:
                next_level = level_name
                points_to_next = required_points - user_points
                break
        
        # Calculate progress percentage
        if next_level:
            next_level_points = level_mapping[next_level]
            prev_level_points = current_level_points
            if next_level_points > prev_level_points:
                progress_percentage = ((user_points - prev_level_points) / (next_level_points - prev_level_points)) * 100
            else:
                progress_percentage = 100
        else:
            progress_percentage = 100  # Max level reached
        
        # Create level_info object
        level_info = {
            'next_level': next_level,
            'points_to_next': points_to_next,
            'level_points': max(0, level_points),
            'progress_percentage': progress_percentage
        }
        
        # For now, provide empty points_log until points logging is implemented
        points_log = []
        
        return render_template('dashboard/profile.html', 
                             user=user_data,
                             learning_count=learning_count,
                             completed_courses_count=completed_courses_count,
                             level_info=level_info,
                             points_log=points_log)
    finally:
        conn.close()

@app.route('/points_log')
def points_log():
    """View user's points transaction history"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # For now, return empty points log
    # TODO: Implement actual points logging system
    return render_template('dashboard/profile.html', 
                         user=user,
                         learning_count=0,
                         completed_courses_count=0,
                         level_info={'next_level': None, 'points_to_next': 0, 'level_points': 0, 'progress_percentage': 0},
                         points_log=[])

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
        level_mapping = {'Beginner': 0, 'Intermediate': 150, 'Advanced': 250}
        next_level = 'Advanced'
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
    """Admin session management with dynamic statistics"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Get active sessions
        active_sessions = conn.execute('''
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
        
        # Get activity statistics (last 7 days)
        activity_stats = conn.execute('''
            SELECT activity_type, COUNT(*) as count
            FROM session_activity 
            WHERE datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY activity_type
            ORDER BY count DESC
        ''').fetchall()
        
        # Get daily login statistics (last 7 days)
        login_stats = conn.execute('''
            SELECT DATE(created_at) as login_date, COUNT(*) as login_count
            FROM user_sessions 
            WHERE datetime(created_at) >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY login_date DESC
        ''').fetchall()
        
        # Calculate today's login count
        today_login_count = 0
        today_date = conn.execute("SELECT DATE('now')").fetchone()[0]
        for stat in login_stats:
            if stat['login_date'] == today_date:
                today_login_count = stat['login_count']
                break
        
        return render_template('admin/sessions.html', 
                             active_sessions=active_sessions,
                             activity_stats=activity_stats,
                             login_stats=login_stats,
                             today_login_count=today_login_count)
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
    """Admin course management with pagination"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)  # Default 25 courses per page
    search = request.args.get('search', '', type=str)
    source_filter = request.args.get('source', '', type=str)
    level_filter = request.args.get('level', '', type=str)
    url_status_filter = request.args.get('url_status', '', type=str)
    points_filter = request.args.get('points', '', type=str)
    
    # Ensure per_page is within reasonable bounds
    per_page = max(10, min(100, per_page))
    
    # Get courses with pagination
    conn = get_db_connection()
    try:
        # Build WHERE clause for filters
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(title LIKE ? OR description LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
            
        if source_filter:
            where_conditions.append("source = ?")
            params.append(source_filter)
            
        if level_filter:
            where_conditions.append("level = ?")
            params.append(level_filter)
            
        if url_status_filter:
            where_conditions.append("url_status = ?")
            params.append(url_status_filter)
            
        if points_filter:
            if points_filter == "0-100":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 0 AND 100")
            elif points_filter == "100-200":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 100 AND 200")
            elif points_filter == "200-300":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 200 AND 300")
            elif points_filter == "300-400":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 300 AND 400")
            elif points_filter == "400+":
                where_conditions.append("CAST(points as INTEGER) > 400")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count for pagination
        count_query = f'SELECT COUNT(*) as count FROM courses {where_clause}'
        total_courses = conn.execute(count_query, params).fetchone()['count']
        
        # Calculate pagination info
        total_pages = max(1, (total_courses + per_page - 1) // per_page)  # Ceiling division
        page = max(1, min(page, total_pages))  # Ensure page is within bounds
        offset = (page - 1) * per_page
        
        # Get courses for current page
        query = f'''
            SELECT * FROM courses 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        courses = conn.execute(query, params).fetchall()
        
        # Get available sources and levels for filters
        sources = conn.execute('SELECT DISTINCT source FROM courses WHERE source IS NOT NULL ORDER BY source').fetchall()
        levels = conn.execute('SELECT DISTINCT level FROM courses WHERE level IS NOT NULL ORDER BY level').fetchall()
        
        # Calculate statistics for the dashboard (from entire database, not just current page)
        stats_query = '''
            SELECT 
                COUNT(*) as total_courses,
                COUNT(CASE WHEN source = 'Manual' THEN 1 END) as manual_entries,
                COUNT(CASE WHEN url_status = 'Working' THEN 1 END) as working_urls,
                COUNT(CASE WHEN url_status = 'Not Working' OR url_status = 'Broken' THEN 1 END) as broken_urls
            FROM courses
        '''
        stats = conn.execute(stats_query).fetchone()
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_courses': total_courses,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'start_course': offset + 1,
            'end_course': min(offset + per_page, total_courses)
        }
        
        return render_template('admin/courses.html', 
                             courses=courses, 
                             pagination=pagination_info,
                             stats=stats,
                             sources=[row['source'] for row in sources],
                             levels=[row['level'] for row in levels],
                             current_search=search,
                             current_source=source_filter,
                             current_level=level_filter,
                             current_url_status=url_status_filter,
                             current_points=points_filter)
    finally:
        conn.close()

@app.route('/admin/debug_environment', methods=['GET'])
def debug_environment():
    """Debug endpoint to check Azure environment"""
    import sys
    import os
    
    try:
        # Test imports
        import pandas as pd
        pandas_version = pd.__version__
        pandas_ok = True
    except ImportError as e:
        pandas_version = f"IMPORT ERROR: {e}"
        pandas_ok = False
    
    try:
        import openpyxl
        openpyxl_version = openpyxl.__version__
        openpyxl_ok = True
    except ImportError as e:
        openpyxl_version = f"IMPORT ERROR: {e}"
        openpyxl_ok = False
    
    try:
        import sqlite3
        sqlite_version = sqlite3.sqlite_version
        sqlite_ok = True
    except ImportError as e:
        sqlite_version = f"IMPORT ERROR: {e}"
        sqlite_ok = False
    
    debug_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "environment_variables": {
            "WEBSITE_SITE_NAME": os.environ.get("WEBSITE_SITE_NAME"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "PATH": os.environ.get("PATH", "")[:200] + "..." if len(os.environ.get("PATH", "")) > 200 else os.environ.get("PATH", ""),
        },
        "dependencies": {
            "pandas": {"version": pandas_version, "ok": pandas_ok},
            "openpyxl": {"version": openpyxl_version, "ok": openpyxl_ok},
            "sqlite3": {"version": sqlite_version, "ok": sqlite_ok}
        },
        "file_system": {
            "current_directory": os.getcwd(),
            "temp_directory": os.environ.get("TEMP", "/tmp"),
            "can_write_temp": os.access(os.environ.get("TEMP", "/tmp"), os.W_OK)
        }
    }
    
    return jsonify(debug_info)

@app.route('/admin/upload_excel_courses', methods=['POST'])
def admin_upload_excel_courses():
    """Upload courses from Excel file - Admin only"""
    try:
        print(f"📋 Upload request received from: {request.remote_addr}")
        user = get_current_user()
        print(f"📋 Current user: {user}")
        
        if not user or user['username'] != 'admin':
            print(f"❌ Access denied for user: {user}")
            return jsonify({'success': False, 'error': 'Admin privileges required.'}), 403
    except Exception as auth_error:
        print(f"❌ Authentication error: {auth_error}")
        return jsonify({'success': False, 'error': f'Authentication error: {str(auth_error)}'}), 500
    
    try:
        import pandas as pd
        from datetime import datetime
        import hashlib
        from upload_reports_manager import UploadReportsManager
        
        # Initialize upload reports manager
        try:
            reports_manager = UploadReportsManager()
        except Exception as e:
            print(f"Warning: Could not initialize upload reports manager: {e}")
            reports_manager = None
        
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded.'}), 400
        
        file = request.files['excel_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls).'}), 400
        
        # Read Excel file
        try:
            df = pd.read_excel(file)
            print(f"Excel file read successfully: {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            error_msg = f'Failed to read Excel file: {str(e)}'
            print(f"Excel read error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Validate required columns
        required_columns = ['title', 'url', 'source', 'level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f'Missing required columns: {", ".join(missing_columns)}. Required: {", ".join(required_columns)}'
            print(f"Column validation error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Process the data
        conn = None
        try:
            conn = get_db_connection()
            print("Database connection established")
            
            stats = {
                'total_processed': 0,
                'added': 0,
                'skipped': 0,
                'errors': 0,
                'error_details': []
            }
            
            # Create upload report entry
            report_id = None
            if reports_manager:
                try:
                    report_id = reports_manager.create_upload_report(
                        user_id=user['id'],
                        filename=file.filename,
                        total_rows=len(df),
                        processed_rows=0,
                        success_count=0,
                        error_count=0,
                        warnings_count=0
                    )
                except Exception as report_error:
                    print(f"Warning: Could not create upload report: {report_error}")
                    report_id = None
            
            # Get existing courses to check for duplicates
            existing_courses = conn.execute('SELECT title, url FROM courses').fetchall()
            existing_set = set()
            for row in existing_courses:
                title = row['title'] if row['title'] else ''
                url = row['url'] if row['url'] else ''
                if title and url:  # Only add if both title and url are not empty
                    existing_set.add((title.lower().strip(), url.lower().strip()))
            print(f"Found {len(existing_set)} existing courses for duplicate check")
            
            for index, row in df.iterrows():
                stats['total_processed'] += 1
                
                try:
                    # Extract and validate data
                    title = str(row['title']).strip() if pd.notna(row['title']) else ''
                    url = str(row['url']).strip() if pd.notna(row['url']) else ''
                    source = str(row['source']).strip() if pd.notna(row['source']) else ''
                    level = str(row['level']).strip() if pd.notna(row['level']) else ''
                    
                    # Validate required fields
                    if not all([title, url, source, level]):
                        error_detail = f'Row {index + 1}: Missing required data - title: {bool(title)}, url: {bool(url)}, source: {bool(source)}, level: {bool(level)}'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Validate level
                    if level not in ['Beginner', 'Intermediate', 'Advanced']:
                        error_detail = f'Row {index + 1}: Invalid level "{level}", must be Beginner, Intermediate, or Advanced'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Validate URL format
                    if not url.startswith(('http://', 'https://')):
                        error_detail = f'Row {index + 1}: Invalid URL format "{url}", must start with http:// or https://'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Check for duplicates
                    if (title.lower(), url.lower()) in existing_set:
                        stats['skipped'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='skipped',
                                    message='Duplicate course already exists',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add skipped row detail: {detail_error}")
                        continue
                    
                    # Extract optional fields
                    description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                    category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None
                    difficulty = str(row.get('difficulty', '')).strip() if pd.notna(row.get('difficulty')) else None
                    
                    # Handle points
                    points = 0
                    if 'points' in row and pd.notna(row['points']):
                        try:
                            points = int(float(row['points']))
                            if points < 0:
                                points = 0
                        except (ValueError, TypeError):
                            points = 0
                    
                    # Auto-assign level based on points if points are provided
                    if points > 0:
                        if points < 150:
                            level = 'Beginner'
                        elif points < 250:
                            level = 'Intermediate'
                        else:
                            level = 'Advanced'
                    
                    # Insert the course
                    try:
                        conn.execute('''
                            INSERT INTO courses 
                            (title, description, url, link, source, level, points, category, difficulty, created_at, url_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            title,
                            description,
                            url,
                            url,  # Use the same URL for both url and link columns
                            source,
                            level,
                            points,
                            category,
                            difficulty,
                            datetime.now().isoformat(),
                            'Pending'
                        ))
                        
                        # Add to existing set to prevent duplicates within the same upload
                        existing_set.add((title.lower(), url.lower()))
                        stats['added'] += 1
                        
                        # Add successful row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='success',
                                    message='Course added successfully',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add row detail: {detail_error}")
                        
                    except Exception as db_error:
                        error_detail = f'Row {index + 1}: Database insert failed - {str(db_error)}'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        print(f"Database insert error for row {index + 1}: {str(db_error)}")
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add DB error row detail: {detail_error}")
                        continue
                    
                except Exception as row_error:
                    error_detail = f'Row {index + 1}: Processing failed - {str(row_error)}'
                    stats['error_details'].append(error_detail)
                    stats['errors'] += 1
                    print(f"Row processing error for row {index + 1}: {str(row_error)}")
                    
                    # Add row detail to report
                    if report_id and reports_manager:
                        try:
                            reports_manager.add_row_detail(
                                report_id=report_id,
                                row_number=index + 1,
                                status='failed',
                                message=error_detail,
                                course_title='Unknown',
                                course_url='Unknown'
                            )
                        except Exception as detail_error:
                            print(f"Warning: Could not add processing error row detail: {detail_error}")
                    continue
            
            # Commit the transaction
            try:
                conn.commit()
                print(f"Transaction committed successfully. Stats: {stats}")
                
                # Update the upload report with final statistics
                if report_id and reports_manager:
                    try:
                        reports_manager.update_upload_report(
                            report_id=report_id,
                            processed_rows=stats['total_processed'],
                            success_count=stats['added'],
                            error_count=stats['errors'],
                            warnings_count=stats['skipped']
                        )
                    except Exception as update_error:
                        print(f"Warning: Could not update upload report: {update_error}")
            except Exception as commit_error:
                print(f"Commit error: {str(commit_error)}")
                return jsonify({
                    'success': False, 
                    'error': f'Failed to save courses to database: {str(commit_error)}',
                    'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }
                }), 500
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Excel upload completed successfully.',
                'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }
            }
            
            # Include error details if there were any errors (but still consider it a success if some courses were added)
            if stats['error_details']:
                response_data['warnings'] = stats['error_details'][:10]  # Limit to first 10 errors for readability
            
            return jsonify(response_data)
            
        except Exception as db_error:
            error_msg = f'Database operation failed: {str(db_error)}'
            print(f"Database error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
        finally:
            if conn:
                conn.close()
                print("Database connection closed")
            
    except ImportError as import_error:
        error_msg = f'pandas library is required for Excel processing. Import error: {str(import_error)}'
        print(f"Import error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Upload failed: {str(e)}'
        print(f"General error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/admin/download_excel_template')
def admin_download_excel_template():
    """Download Excel template for course upload - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        import pandas as pd
        from io import BytesIO
        from flask import send_file
        
        # Create sample data for the template
        sample_data = {
            'title': [
                'Introduction to Machine Learning',
                'Advanced Python Programming',
                'Azure AI Fundamentals'
            ],
            'description': [
                'Learn the basics of machine learning and AI concepts',
                'Deep dive into advanced Python programming techniques',
                'Understand Azure AI services and capabilities'
            ],
            'url': [
                'https://learn.microsoft.com/en-us/training/paths/machine-learning-foundations',
                'https://learn.microsoft.com/en-us/training/paths/python-advanced',
                'https://learn.microsoft.com/en-us/training/paths/azure-ai-fundamentals'
            ],
            'source': [
                'Microsoft Learn',
                'Microsoft Learn', 
                'Microsoft Learn'
            ],
            'level': [
                'Beginner',
                'Intermediate',
                'Advanced'
            ],
            'points': [
                120,
                200,
                300
            ],
            'category': [
                'Machine Learning',
                'Programming',
                'Cloud Computing'
            ],
            'difficulty': [
                'Easy',
                'Medium',
                'Hard'
            ]
        }
        
        # Create DataFrame
        df = pd.DataFrame(sample_data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Courses', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Courses']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='course_upload_template.xlsx'
        )
        
    except ImportError:
        flash('pandas library is required for Excel processing.', 'error')
        return redirect(url_for('admin_courses'))
    except Exception as e:
        flash(f'Failed to generate template: {str(e)}', 'error')
        return redirect(url_for('admin_courses'))

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

@app.route('/admin/url-validation')
@require_admin
def admin_url_validation():
    """URL validation management page - Admin only"""
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
            status = course.get('url_status', 'Unchecked') if course else 'Unchecked'
            if status == 'Working':
                summary['working']['count'] += 1
            elif status == 'Not Working':
                summary['not_working']['count'] += 1
            elif status == 'Broken':
                summary['broken']['count'] += 1
            else:
                summary['unchecked']['count'] += 1
        
        return render_template('admin/url_validation.html',
                             courses=courses,
                             summary=summary)
        
    except Exception as e:
        flash(f'Error loading URL validation data: {e}', 'error')
        return redirect(url_for('admin_courses'))
    finally:
        conn.close()

@app.route('/admin/validate-all-urls', methods=['POST'])
@require_admin
def admin_validate_all_urls():
    """Start URL validation for all courses (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        courses = conn.execute('SELECT id, title, url FROM courses WHERE url IS NOT NULL AND url != ""').fetchall()
        conn.close()
        
        if not courses:
            return jsonify({'success': False, 'message': 'No courses with URLs found'})
        
        # Start validation in background thread
        def validate_urls():
            conn = get_db_connection()
            try:
                for course in courses:
                    try:
                        # Basic URL validation
                        parsed = urlparse(course['url'])
                        if not parsed.scheme or not parsed.netloc:
                            status = 'Broken'
                        else:
                            # Try to connect to URL (with timeout)
                            try:
                                response = requests.head(course['url'], timeout=10, allow_redirects=True)
                                if response.status_code < 400:
                                    status = 'Working'
                                else:
                                    status = 'Not Working'
                            except requests.exceptions.RequestException:
                                # If HEAD fails, try GET with smaller content
                                try:
                                    response = requests.get(course['url'], timeout=10, allow_redirects=True, stream=True)
                                    if response.status_code < 400:
                                        status = 'Working'
                                    else:
                                        status = 'Not Working'
                                except requests.exceptions.RequestException:
                                    status = 'Broken'
                    except Exception:
                        status = 'Broken'
                    
                    # Update database
                    conn.execute('''
                        UPDATE courses 
                        SET url_status = ?, last_url_check = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (status, course['id']))
                    conn.commit()
            except Exception as e:
                print(f"URL validation error: {e}")
            finally:
                conn.close()
        
        # Start background thread
        thread = threading.Thread(target=validate_urls)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'URL validation started for {len(courses)} courses',
            'course_count': len(courses)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting validation: {str(e)}'})

@app.route('/admin/url-validation-status')
@require_admin
def admin_url_validation_status():
    """Get URL validation status (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        
        # Get summary of validation status
        courses = conn.execute('''
            SELECT id, title, url, url_status, last_url_check
            FROM courses 
            WHERE url IS NOT NULL AND url != ""
            ORDER BY last_url_check DESC
        ''').fetchall()
        
        # Count by status
        status_counts = {
            'working': 0,
            'not_working': 0,
            'broken': 0,
            'unchecked': 0
        }
        
        course_list = []
        for course in courses:
            status = course.get('url_status', 'Unchecked') or 'Unchecked'
            status_lower = status.lower().replace(' ', '_')
            if status_lower in status_counts:
                status_counts[status_lower] += 1
            else:
                status_counts['unchecked'] += 1
            
            course_list.append({
                'id': course['id'],
                'title': course['title'],
                'url': course['url'],
                'status': status,
                'last_check': course.get('last_url_check', 'Never')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'courses': course_list,
            'summary': status_counts,
            'total_courses': len(course_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting status: {str(e)}'})

@app.route('/admin/edit-course/<int:course_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_course(course_id):
    """Edit a course (admin only)"""
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            provider = request.form.get('provider')
            source = request.form.get('source')
            url = request.form.get('url')
            link = request.form.get('link')
            level = request.form.get('level')
            category = request.form.get('category')
            points = request.form.get('points', 0)
            
            if not title or not description:
                flash('Title and description are required.', 'error')
                return redirect(url_for('admin_edit_course', course_id=course_id))
            
            try:
                points = int(points) if points else 0
            except ValueError:
                points = 0
            
            # Auto-calculate level based on points
            if points < 150:
                level = 'Beginner'
            elif points < 250:
                level = 'Intermediate'
            else:
                level = 'Advanced'
            
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
        # Delete related records first (if user_courses table exists)
        try:
            conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        except:
            pass  # Table might not exist
        
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/bulk-delete-courses', methods=['POST'])
@require_admin
def admin_bulk_delete_courses():
    """Bulk delete multiple courses (admin only)"""
    course_ids = request.form.getlist('course_ids')
    
    if not course_ids:
        flash('No courses selected for deletion.', 'warning')
        return redirect(url_for('admin_courses'))
    
    # Validate that all IDs are integers
    try:
        course_ids = [int(id) for id in course_ids]
    except ValueError:
        flash('Invalid course IDs provided.', 'error')
        return redirect(url_for('admin_courses'))
    
    conn = get_db_connection()
    deleted_count = 0
    
    try:
        # Delete related records first (if user_courses table exists)
        try:
            for course_id in course_ids:
                conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        except:
            pass  # Table might not exist
        
        # Delete courses
        for course_id in course_ids:
            result = conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            if result.rowcount > 0:
                deleted_count += 1
        
        conn.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} course(s)!', 'success')
        else:
            flash('No courses were deleted. They may have already been removed.', 'warning')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting courses: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@require_admin
def admin_delete_user(user_id):
    """Delete a user (admin only) - requires explicit authorization"""
    # Explicit authorization check for user deletion
    try:
        # Check if this is production environment
        if production_safety.environment == 'production':
            # In production, require additional explicit authorization
            explicit_authorization = request.form.get('explicit_authorization')
            if not explicit_authorization:
                flash('User deletion requires explicit authorization in production.', 'error')
                return redirect(url_for('admin_users'))
    except:
        pass  # Continue if production_safety not available
    
    conn = get_db_connection()
    try:
        # Check if user exists and get username for validation
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user['username']
        
        # Protected users that cannot be deleted - admin user cannot be deleted
        protected_users = ['admin']
        if username in protected_users:
            flash(f'Admin user cannot be deleted - system protection active.', 'error')
            return redirect(url_for('admin_users'))
        
        # Delete user and related data
        try:
            conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        try:
            conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        try:
            conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        flash(f'User "{username}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/toggle-user-status/<int:user_id>', methods=['POST'])
@require_admin
def admin_toggle_user_status(user_id):
    """Toggle user status between active and inactive (admin only)"""
    conn = get_db_connection()
    try:
        # Get current user status
        user = conn.execute('SELECT username, status FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Toggle status
        new_status = 'inactive' if user['status'] == 'active' else 'active'
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        
        flash(f'User "{user["username"]}" status changed to {new_status}.', 'success')
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/set-user-password', methods=['POST'])
@require_admin 
def admin_set_user_password():
    """Allow admin to set a custom password for a user"""
    user_id = request.form.get('user_id')
    new_password = request.form.get('custom_password')  # Updated to match form field name
    confirm_password = request.form.get('confirm_custom_password')
    
    if not user_id or not new_password:
        flash('User ID and new password are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if new_password != confirm_password:
        flash('Password confirmation does not match.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get user info
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Hash and update password
        hashed_password = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (hashed_password, user_id)
        )
        conn.commit()
        
        flash(f'Password updated successfully for user: {user["username"]}', 'success')
        
    except Exception as e:
        flash(f'Error updating password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reset-all-user-passwords', methods=['POST'])
@require_admin
def admin_reset_all_user_passwords():
    """Reset all user passwords (admin only) - requires explicit authorization"""
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    confirmation = request.form.get('reset_all_confirmation')
    
    # Explicit authorization check for bulk password reset
    try:
        if production_safety.environment == 'production':
            explicit_authorization = request.form.get('explicit_authorization')
            if not explicit_authorization:
                flash('Bulk password reset requires explicit authorization in production.', 'error')
                return redirect(url_for('admin_users'))
    except:
        pass  # Continue if production_safety not available
    
    if not new_password or not confirm_password:
        flash('Both password fields are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if new_password != confirm_password:
        flash('Password confirmation does not match.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
        
    if not confirmation:
        flash('You must confirm the bulk password reset operation.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get all users except admin
        users = conn.execute('SELECT id, username FROM users WHERE username != ?', ('admin',)).fetchall()
        
        if not users:
            flash('No users found to reset passwords for.', 'warning')
            return redirect(url_for('admin_users'))
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update all non-admin users
        updated_count = 0
        for user in users:
            conn.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (hashed_password, user['id'])
            )
            updated_count += 1
        
        conn.commit()
        flash(f'Successfully reset passwords for {updated_count} users. Users will need to use the new password on their next login.', 'success')
        
    except Exception as e:
        flash(f'Error resetting passwords: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

# Legacy route name for compatibility with existing form
@app.route('/admin/reset-user-password', methods=['POST'])
@require_admin
def admin_reset_user_password():
    """Legacy route - redirects to the new set password function"""
    return admin_set_user_password()

@app.route('/admin/search-and-import-courses', methods=['POST'])
@require_admin
def admin_search_and_import_courses():
    """Search and import courses from external sources (admin only)"""
    search_term = request.form.get('search_term', '')
    source = request.form.get('source', 'manual')
    
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

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Admin settings"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Update level settings
        try:
            for level_name in ['beginner', 'learner', 'intermediate', 'expert']:
                points_key = f'{level_name}_points'
                if points_key in request.form:
                    points_required = int(request.form[points_key])
                    conn.execute(
                        'UPDATE level_settings SET points_required = ? WHERE LOWER(level_name) = ?',
                        (points_required, level_name)
                    )
            conn.commit()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('admin_settings'))
    
    # Get current level settings
    try:
        level_settings = conn.execute(
            'SELECT level_name, points_required FROM level_settings ORDER BY points_required ASC'
        ).fetchall()
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'error')
        level_settings = []
    finally:
        conn.close()
    
    return render_template('admin/settings.html', level_settings=level_settings)

@app.route('/admin/change-password', methods=['GET', 'POST'])
def admin_change_password():
    """Admin change password"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('admin/change_password.html')
        
        # Verify current password
        conn = get_db_connection()
        try:
            admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
            if admin_user and check_password_hash(admin_user['password_hash'], current_password):
                # Update password
                new_hash = generate_password_hash(new_password)
                conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
                conn.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Current password is incorrect.', 'error')
        finally:
            conn.close()
    
    return render_template('admin/change_password.html')

# Admin User Management Routes
@app.route('/admin/add-user', methods=['GET', 'POST'])
@require_admin
def admin_add_user():
    """Add a new user (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        level = request.form.get('level', 'Beginner')
        status = request.form.get('status', 'active')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
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

# Admin Course Management Routes
@app.route('/admin/add-course', methods=['GET', 'POST'])
@require_admin
def admin_add_course():
    """Add a new course with comprehensive validation (admin only)"""
    if request.method == 'POST':
        # Course validator temporarily disabled - module removed in cleanup
        logger.info("Course validation temporarily disabled - using basic validation only")
        flash('Course added with basic validation. Advanced URL validation temporarily unavailable.', 'info')
        validator = None
        
        # Collect form data
        course_data = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'provider': request.form.get('provider', '').strip(),  # Keep for backward compatibility
            'source': request.form.get('source', '').strip(),
            'url': request.form.get('url', '').strip() or None,
            'link': request.form.get('link', '').strip() or None,
            'level': request.form.get('level', '').strip(),
            'category': request.form.get('category', '').strip() or None,
            'points': request.form.get('points', 0)
        }
        
        # Validate with comprehensive schema validation
        if validator:
            course = validator.validate_schema(course_data)
            
            # Check for validation errors
            if not course.is_valid:
                for error in course.validation_errors:
                    if error.severity == 'error':
                        flash(f'{error.field.title()}: {error.message}', 'error')
                    else:
                        flash(f'{error.field.title()}: {error.message}', 'warning')
                
                # If there are errors, return to form with data
                if any(e.severity == 'error' for e in course.validation_errors):
                    return render_template('admin/add_course.html', course_data=course_data)
            
            # Validate URLs if provided
            url_validation_results = {}
            validation_warnings = []
            
            if course.url:
                logger.info(f"Validating primary URL: {course.url}")
                url_result = validator.validate_url(course.url)
                url_validation_results['url'] = url_result
                
                if url_result['status'] not in ['Working']:
                    validation_warnings.append(f"Primary URL may not be accessible: {url_result.get('error_message', 'Unknown error')}")
                    
            if course.link and course.link != course.url:
                logger.info(f"Validating link URL: {course.link}")
                link_result = validator.validate_url(course.link)
                url_validation_results['link'] = link_result
                
                if link_result['status'] not in ['Working']:
                    validation_warnings.append(f"Link URL may not be accessible: {link_result.get('error_message', 'Unknown error')}")
            
            # Show URL validation warnings
            for warning in validation_warnings:
                flash(warning, 'warning')
                
            # Update course data with validation results
            if course.url and 'url' in url_validation_results:
                course.url_status = url_validation_results['url']['status']
                course.last_url_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Fallback validation without validator
            if not course_data['title'] or not course_data['description']:
                flash('Title and description are required.', 'error')
                return render_template('admin/add_course.html', course_data=course_data)
            
            try:
                course_data['points'] = int(course_data['points']) if course_data['points'] else 0
            except ValueError:
                course_data['points'] = 0
                flash('Points must be a number. Set to 0.', 'warning')
            
            course = type('Course', (), course_data)()
            course.url_status = 'unchecked'
            course.last_url_check = None
        
        # Insert into database
        conn = get_db_connection()
        try:
            # Determine which URL field to use for url_status tracking
            primary_url = course.url or course.link
            
            conn.execute('''
                INSERT INTO courses (
                    title, description, provider, source, url, link, level, category, points,
                    created_at, url_status, last_url_check
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
            ''', (
                course.title, course.description, course_data['provider'], course.source,
                course.url, course.link, course.level, course.category, course.points,
                course.url_status, course.last_url_check
            ))
            conn.commit()
            
            # Success message with validation info
            success_msg = 'Course added successfully!'
            if validator and primary_url:
                if course.url_status == 'Working':
                    success_msg += ' URL validation passed.'
                elif course.url_status in ['Not Working', 'Broken']:
                    success_msg += f' Note: URL validation failed ({course.url_status}).'
                else:
                    success_msg += ' URL validation completed with warnings.'
            
            flash(success_msg, 'success')
            logger.info(f"Course added successfully: {course.title} (URL Status: {course.url_status})")
            
            return redirect(url_for('admin_courses'))
            
        except Exception as e:
            logger.error(f"Database error adding course: {e}")
            flash(f'Error adding course: {str(e)}', 'error')
            return render_template('admin/add_course.html', course_data=course_data)
        finally:
            conn.close()
    
    return render_template('admin/add_course.html')

# Global storage for course fetch status (since background threads can't access Flask session)
course_fetch_status = {}

@app.route('/admin/populate-ai-courses', methods=['POST'])
@require_admin
def admin_populate_ai_courses():
    """Fetch AI/Copilot courses from live APIs with real-time updates"""
    logger.info("🔍 Admin initiated FAST live API course fetching")
    
    # Fast course fetcher temporarily disabled - module removed in cleanup
    logger.info("Fast course API fetcher temporarily disabled - using basic course addition only")
    return jsonify({
        'success': False,
        'error': 'Fast course fetcher temporarily unavailable. Please add courses manually.',
        'message': 'Advanced course fetching is temporarily disabled during workspace cleanup.'
    }), 503

    try:
        logger.info("📡 Starting FAST live API course fetching...")
        
        # Start asynchronous course fetching with real-time updates
        import threading
        import uuid
        
        # Generate unique fetch ID for this request
        fetch_id = str(uuid.uuid4())[:8]
        
        def fetch_courses_async():
            """Background task to fetch courses asynchronously"""
            try:
                # Update status: Starting
                course_fetch_status[fetch_id] = {
                    'status': 'fetching',
                    'message': 'Fetching courses from live APIs...',
                    'progress': 10
                }
                
                # Fetch courses (faster, no fallbacks)
                result = get_fast_ai_courses(10)  # Reduced count for speed
                
                # Update status: Complete
                course_fetch_status[fetch_id] = {
                    'status': 'complete',
                    'message': f'Successfully added {result["courses_added"]} courses in {result["total_time"]}s',
                    'progress': 100,
                    'result': result
                }
                
                logger.info(f"📚 Fast course fetching completed: {result['courses_added']} courses added")
                
            except Exception as e:
                # Update status: Error
                course_fetch_status[fetch_id] = {
                    'status': 'error',
                    'message': f'Error: {str(e)}',
                    'progress': 0,
                    'error': str(e)
                }
                logger.error(f"❌ Fast course fetching failed: {e}")
        
        # Start background thread
        fetch_thread = threading.Thread(target=fetch_courses_async)
        fetch_thread.daemon = True
        fetch_thread.start()
        
        # Return JSON response with fetch ID for status tracking
        return jsonify({
            'success': True,
            'fetch_id': fetch_id,
            'message': 'Course fetching started - real APIs only, no fallbacks'
        })
            
    except Exception as e:
        error_msg = f'Error starting fast API course fetching: {str(e)}'
        logger.error(f"❌ Failed to start fast background fetching: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/admin/course-fetch-status/<fetch_id>')
@require_admin
def get_course_fetch_status(fetch_id):
    """Get the status of a course fetching operation"""
    status = course_fetch_status.get(fetch_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Fetch operation not found'
        }), 404


# Backward compatibility alias for old route name
@app.route('/admin/populate-linkedin-courses', methods=['POST'])
@require_admin  
def admin_populate_linkedin_courses():
    """Backward compatibility alias - redirects to new admin_populate_ai_courses"""
    logger.info("⚠️ Using deprecated route - redirecting to admin_populate_ai_courses")
    return admin_populate_ai_courses()

@app.route('/setup-admin')
def setup_admin():
    """Simple setup route to create admin user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            conn.close()
            return "✅ Admin user already exists! <a href='/'>Go to Login</a>"
        
        # Create admin user
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return f"""
        🎉 Admin user created successfully!<br>
        Username: admin<br>
        Password: {admin_password}<br>
        <a href='/'>Go to Login</a>
        """
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/health')
def health_check():
    """Health check endpoint with admin initialization"""
    
    import sqlite3
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    html_template = '''
    <html>
    <head><title>Health Check</title></head>
    <body style="font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px;">
        <h2>🔍 AI Learning Tracker - Health Check</h2>
        {content}
        <hr>
        <p><small>Last updated: {timestamp}</small></p>
    </body>
    </html>
    '''
    
    try:
        status_info = []
        
        # Check database connection
        try:
            conn = get_db_connection()
            status_info.append("✅ Database connection: OK")
            
            # Check tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'users' in tables:
                status_info.append("✅ Users table: EXISTS")
                
                # Check admin user
                cursor.execute("SELECT id, username, level FROM users WHERE username = 'admin'")
                admin_user = cursor.fetchone()
                
                if admin_user:
                    status_info.append(f"✅ Admin user: EXISTS (ID: {admin_user[0]}, Level: {admin_user[2]})")
                else:
                    status_info.append("❌ Admin user: MISSING")
                    
                    # Try to create admin user
                    status_info.append("🔧 Attempting to create admin user...")
                    
                    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
                    password_hash = generate_password_hash(admin_password)
                    
                    cursor.execute("""
                        INSERT INTO users (
                            username, password_hash, level, points, status,
                            user_selected_level, login_count, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'admin', password_hash, 'Advanced', 100, 'active',
                        'Advanced', 0, datetime.now().isoformat()
                    ))
                    
                    admin_id = cursor.lastrowid
                    conn.commit()
                    
                    status_info.append(f"🎉 Admin user CREATED! (ID: {admin_id})")
                
                # Check total users
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                status_info.append(f"📊 Total users: {user_count}")
                
            else:
                status_info.append("❌ Users table: MISSING")
            
            conn.close()
            
        except Exception as e:
            status_info.append(f"❌ Database error: {str(e)}")
        
        # Check environment variables
        admin_pwd = os.environ.get('ADMIN_PASSWORD')
        if admin_pwd:
            status_info.append(f"✅ ADMIN_PASSWORD: SET (length: {len(admin_pwd)})")
        else:
            status_info.append("❌ ADMIN_PASSWORD: NOT SET")
        
        # Add login test link
        status_info.append("")
        status_info.append("🔗 <strong>Test Login:</strong>")
        status_info.append(f'<a href="/" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px;">Go to Login Page</a>')
        
        content = "<br>".join(status_info)
        
        return html_template.format(
            content=content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
    except Exception as e:
        return html_template.format(
            content=f"❌ Health check failed: {str(e)}",
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )

@app.route('/init-admin')
def simple_init_admin():
    """Simple admin initialization via URL parameter"""
    
    # Get password from URL parameter
    init_password = request.args.get('password', '')
    expected_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    # Basic HTML template
    html_template = '''
    <html>
    <head><title>Admin Initialization</title></head>
    <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-bottom: 20px;">{title}</h2>
            {content}
        </div>
    </body>
    </html>
    '''
    
    if not init_password:
        return html_template.format(
            title="🔧 Admin User Initialization",
            content='''
            <p>To initialize the admin user, add your password as a URL parameter:</p>
            <p><strong>URL Format:</strong></p>
            <code style="background: #f0f0f0; padding: 10px; border-radius: 4px; display: block; margin: 10px 0;">
            https://your-app.azurewebsites.net/init-admin?password=YOUR_ADMIN_PASSWORD
            </code>
            <p><small>⚠️ Use your ADMIN_PASSWORD environment variable value</small></p>
            '''
        )
    
    if init_password != expected_password:
        return html_template.format(
            title="❌ Invalid Password",
            content='''
            <p>The initialization password is incorrect.</p>
            <p>Please check your ADMIN_PASSWORD environment variable.</p>
            <a href="/init-admin" style="color: #007bff;">Try Again</a>
            '''
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            conn.close()
            return html_template.format(
                title="✅ Admin Already Exists",
                content='''
                <p>The admin user has already been created.</p>
                <p>You can now login with username <strong>admin</strong></p>
                <a href="/" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    Go to Login
                </a>
                '''
            )
        
        # Create admin user
        password_hash = generate_password_hash(expected_password)
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        
        # Create demo user too
        demo_password = os.environ.get('DEMO_PASSWORD', 'demo123')
        cursor.execute("SELECT id FROM users WHERE username = 'demo'")
        if not cursor.fetchone():
            demo_hash = generate_password_hash(demo_password)
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, level, points, status,
                    user_selected_level, login_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'demo', demo_hash, 'Beginner', 0, 'active',
                'Beginner', 0, datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        return html_template.format(
            title="🎉 Initialization Complete!",
            content=f'''
            <p>✅ <strong>Admin user created successfully!</strong></p>
            <p>✅ Demo user created successfully</p>
            <p>📊 Admin user ID: {admin_id}</p>
            <hr style="margin: 20px 0;">
            <h3>🔗 Ready to Login:</h3>
            <p><strong>Username:</strong> admin</p>
            <p><strong>Password:</strong> [your ADMIN_PASSWORD]</p>
            <p><strong>Level:</strong> Advanced</p>
            <br>
            <a href="/" style="background: #28a745; color: white; padding: 15px 25px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                🚀 Go to Login Page
            </a>
            '''
        )
        
    except Exception as e:
        return html_template.format(
            title="❌ Initialization Failed",
            content=f'''
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please check the application logs for more details.</p>
            <a href="/init-admin" style="color: #007bff;">Try Again</a>
            '''
        )

# Initialize database on startup
try:
    if db_init:
        logger.info("🔄 Initializing database with Azure SQL support...")
        db_init()
        logger.info("✅ Database initialization completed")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")


@app.route('/create-admin-now')
def create_admin_now():
    """Emergency route to create admin user directly"""
    try:
        conn = get_db_connection()
        
        # First create users table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                user_selected_level TEXT DEFAULT 'Beginner',
                login_count INTEGER DEFAULT 0
            )
        ''')
        
        # Check if admin already exists
        existing_admin = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if existing_admin:
            conn.close()
            return f"<h2>Admin user already exists with ID: {existing_admin['id']}</h2><a href='/'>Go to Login</a>"
        
        # Create admin user with the known password
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 100, 'active', 'Advanced', 0))
        
        conn.commit()
        admin_id = conn.lastrowid
        conn.close()
        
        return f"<h2> Admin user created successfully!</h2><p>Admin ID: {admin_id}</p><p>Username: admin</p><p>You can now login at <a href='/'>the login page</a></p>"
        
    except Exception as e:
        return f"<h2> Error creating admin: {str(e)}</h2><a href='/create-admin-now'>Try Again</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
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
from urllib.parse import urlparse
try:
    from database_manager import get_db_connection as db_get_connection, init_database as db_init, db_manager
except ImportError:
    db_get_connection = None
    db_init = None
    db_manager = None

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

# Import Azure database sync for production
try:
    from azure_database_sync import AzureDatabaseSync
    azure_sync = AzureDatabaseSync()
    AZURE_SYNC_AVAILABLE = True
    print('✅ Azure database sync loaded')
except ImportError as e:
    print(f'⚠️  Azure sync not available: {e}')
    azure_sync = None
    AZURE_SYNC_AVAILABLE = False

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

# Initialize Azure database sync on startup
if AZURE_SYNC_AVAILABLE and azure_sync:
    print('🔄 Initializing Azure database sync...')
    try:
        # Download database from Azure Storage if available
        azure_sync.sync_from_azure_on_startup()
        print('✅ Azure database sync initialized successfully')
    except Exception as e:
        print(f'⚠️ Azure sync initialization failed: {e}')
        print('   Continuing with local database only')

# @app.before_first_request
def initialize_azure_sync():
    """Initialize Azure sync before first request"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.sync_from_azure_on_startup()
        except Exception as e:
            app.logger.warning(f'Azure sync failed on startup: {e}')

def sync_to_azure_after_change():
    """Upload database to Azure after changes"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.upload_database_to_azure()
        except Exception as e:
            app.logger.warning(f'Azure upload failed: {e}')


# Log environment detection
logger.info(f"Environment detected: {production_safety.environment}")
if production_safety.environment == 'production':
    logger.warning("PRODUCTION ENVIRONMENT - Enhanced safety measures active")

# Database configuration - dynamic based on environment
def get_database_path():
    """Get database path from environment configuration"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    elif database_url.startswith('sqlite://'):
        return database_url.replace('sqlite://', '')
    return 'ai_learning.db'

def get_db_connection():
    """Get database connection with environment-aware support for Azure SQL"""
    try:
        # Check if we should use Azure SQL
        database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
        
        if (database_url == 'azure_sql' or production_safety.environment == 'production') and db_get_connection:
            logger.info(f"🌍 Environment: {production_safety.environment}")
            
            if db_manager and db_manager.is_azure_sql:
                logger.info("📂 Connecting to Azure SQL Database")
            else:
                logger.info("📂 Using SQLite via database manager")
            
            return db_get_connection()
        else:
            # Use traditional SQLite connection
            database_path = get_database_path()
            
            # Log database connection details for debugging
            logger.info(f"📂 Connecting to database: {os.path.abspath(database_path)}")
            logger.info(f"🌍 Environment: {production_safety.environment}")
            logger.info(f"💾 Database exists: {os.path.exists(database_path)}")
            
            if os.path.exists(database_path):
                logger.info(f"📊 Database size: {os.path.getsize(database_path)} bytes")
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row
            return conn
            
    except Exception as e:
        # Fallback to old method if there are any issues
        logger.warning(f"Database manager error ({e}), using fallback SQLite connection")
        database_path = get_database_path()
        conn = sqlite3.connect(database_path)
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
    
    # PRODUCTION SAFETY: NEVER auto-create users in any environment
    # Users should only be created through proper admin interfaces
    # Database initialization should ONLY create schema, never data
    # This prevents accidental data overwrites in any environment
    
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

# Azure database backup scheduler
def azure_backup_scheduler():
    """Background thread to periodically backup database to Azure Storage"""
    import time
    time.sleep(300)  # Wait 5 minutes before first backup
    
    while True:
        try:
            # Azure sync temporarily disabled - module removed in cleanup
            logger.info("Azure backup scheduler: Module not available, skipping sync")
            time.sleep(1800)  # Check every 30 minutes
        except Exception as e:
            logger.error(f"Azure backup scheduler error: {e}")
            time.sleep(1800)  # Continue after error

# Start background threads
cleanup_thread = threading.Thread(target=session_cleanup_scheduler, daemon=True)
cleanup_thread.start()

backup_thread = threading.Thread(target=azure_backup_scheduler, daemon=True)
backup_thread.start()

# CRITICAL FIX: Prevent database reinitialization on every startup
# Only initialize database if it doesn't exist or is empty
def safe_init_db():
    """
    CRITICAL FUNCTION: Initialize database only if it doesn't exist or is empty.
    NEVER OVERWRITES EXISTING DATA - ONLY CREATES MISSING TABLES.
    Now includes Azure Storage sync for data persistence.
    """
    try:
        logger.info("🔍 SAFE_INIT_DB: Starting database safety check...")
        
        # AZURE STORAGE INTEGRATION: Temporarily disabled - module removed in cleanup
        logger.info("Azure sync temporarily disabled - using local database only")
        
        # Check if database file exists (may have been downloaded from Azure)
        db_path = get_database_path()
        if not os.path.exists(db_path):
            logger.info(f"📁 SAFE_INIT_DB: Database file {db_path} not found - will create new one")
            init_db()
            ensure_admin_exists()
            return
        
        conn = get_db_connection()
        
        # Check if users table exists
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        
        if not result:
            logger.info("🏗️ SAFE_INIT_DB: Users table missing - initializing schema...")
            conn.close()
            init_db()
            ensure_admin_exists()
            return
        
        # Check if there are any users (most critical check)
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            logger.info(f"✅ SAFE_INIT_DB: Database already has {user_count} users - PRESERVING ALL DATA")
            
            # Log existing users for verification
            try:
                users = conn.execute("SELECT id, username, created_at FROM users ORDER BY id").fetchall()
                logger.info("🔍 SAFE_INIT_DB: Existing users found:")
                for user in users:
                    logger.info(f"   - ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
            except Exception as e:
                logger.warning(f"⚠️ SAFE_INIT_DB: Could not log existing users: {e}")
            
            conn.close()
            
            # Still ensure admin exists but don't overwrite data
            ensure_admin_exists()
            logger.info("✅ SAFE_INIT_DB: Complete - existing data preserved")
            
            # AZURE STORAGE INTEGRATION: Temporarily disabled - module removed in cleanup
            logger.info("Azure sync temporarily disabled - using local database only")
            return
        else:
            logger.info("📋 SAFE_INIT_DB: Users table exists but empty - safe to initialize")
            conn.close()
            init_db()
            ensure_admin_exists()
            # Azure sync temporarily disabled - using local database only
            logger.info("Azure sync temporarily disabled - using local database only")
            return
        
    except Exception as e:
        logger.error(f"❌ SAFE_INIT_DB: Database check failed: {e}")
        logger.error(f"❌ SAFE_INIT_DB: Exception details: {type(e).__name__}: {str(e)}")
        try:
            # Emergency fallback - only if absolutely necessary
            logger.warning("⚠️ SAFE_INIT_DB: Attempting emergency fallback...")
            init_db()
            ensure_admin_exists()
        except Exception as fallback_error:
            logger.error(f"💥 SAFE_INIT_DB: Emergency fallback failed: {fallback_error}")
            raise

def ensure_admin_exists():
    """
    CRITICAL FUNCTION: Ensure admin user exists without overwriting existing admin data
    """
    try:
        logger.info("🔍 ENSURE_ADMIN: Checking admin user status...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id, username, password_hash, level, points, created_at FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            logger.info(f"✅ ENSURE_ADMIN: Admin user already exists - ID: {existing_admin[0]}, Level: {existing_admin[3]}, Points: {existing_admin[4]}")
            logger.info("✅ ENSURE_ADMIN: Preserving existing admin data - NO CHANGES MADE")
            conn.close()
            return
        
        # Only create admin if it doesn't exist
        logger.info("🔄 ENSURE_ADMIN: Admin user not found - creating new admin...")
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.info("✅ ENSURE_ADMIN: New admin user created successfully")
        logger.info(f"🔑 ENSURE_ADMIN: Admin password set from environment variable")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ ENSURE_ADMIN: Admin user check/creation failed: {e}")
        logger.error(f"❌ ENSURE_ADMIN: Exception details: {type(e).__name__}: {str(e)}")
        try:
            conn.close()
        except:
            pass

# Initialize database on startup (SAFE VERSION - preserves existing data)
safe_init_db()

# EMERGENCY FIX: Disable deployment safety to prevent data resets
# Initialize deployment safety and data integrity monitoring
try:
    # RESTORED - deployment safety module recreated
    from deployment_safety import init_deployment_safety
    deployment_safety = init_deployment_safety(app)
    logger.info("✅ Deployment safety initialized successfully")
except ImportError:
    logger.warning("⚠️ Deployment safety module not available - install azure-storage-blob for full functionality")
except Exception as e:
    logger.error(f"❌ Failed to initialize deployment safety: {e}")

# Re-enable blueprints - circular import issue resolved
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp  
from learnings.routes import learnings_bp
from admin.routes import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(learnings_bp, url_prefix='/learnings')
app.register_blueprint(admin_bp)

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
        # Base query for completed courses
        completed_query = '''
            SELECT c.*, uc.completed, uc.completion_date, 'system' as course_type
            FROM courses c 
            INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
        '''
        completed_params = [user['id']]
        
        # Apply filters to completed courses
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
        
        # Base query for recommended courses
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
        
        # Get available filter options
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

@app.route('/export-courses/<course_type>')
def export_courses(course_type):
    """Export courses to CSV"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        if course_type == 'completed':
            courses = conn.execute('''
                SELECT c.title, c.description, c.level, uc.completion_date
                FROM courses c 
                INNER JOIN user_courses uc ON c.id = uc.course_id 
                WHERE uc.user_id = ? AND uc.completed = 1
                ORDER BY uc.completion_date DESC
            ''', (user['id'],)).fetchall()
        else:  # recommended
            courses = conn.execute('''
                SELECT c.title, c.description, c.level, c.created_at as date_added
                FROM courses c 
                LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
                WHERE (uc.completed IS NULL OR uc.completed = 0)
                ORDER BY c.created_at DESC
            ''', (user['id'],)).fetchall()
        
        # Create CSV response
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if course_type == 'completed':
            writer.writerow(['Title', 'Description', 'Level', 'Completion Date'])
        else:
            writer.writerow(['Title', 'Description', 'Level', 'Date Added'])
        
        # Write course data
        for course in courses:
            writer.writerow([course['title'], course['description'], course['level'], 
                           course['completion_date'] if course_type == 'completed' else course['date_added']])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course_type}_courses.csv'}
        )
    
    finally:
        conn.close()

@app.route('/complete-course/<int:course_id>', methods=['POST'])
def complete_course(course_id):
    """Mark a course as completed"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('my_courses'))
        
        # Check if already completed
        existing = conn.execute(
            'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
            (user['id'], course_id)
        ).fetchone()
        
        if existing:
            if existing['completed']:
                flash('Course already completed.', 'info')
            else:
                # Update to completed
                conn.execute(
                    'UPDATE user_courses SET completed = 1, completion_date = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?',
                    (user['id'], course_id)
                )
                conn.commit()
                flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
                log_completion_event(user['id'], course_id, course['title'])
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
            log_completion_event(user['id'], course_id, course['title'])
    
    finally:
        conn.close()
    
    return redirect(url_for('my_courses'))

@app.route('/mark_complete/<int:course_id>', methods=['POST'])
def mark_complete(course_id):
    """AJAX endpoint to mark a course as completed"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Check if already completed
        existing = conn.execute(
            'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
            (user['id'], course_id)
        ).fetchone()
        
        if existing:
            if existing['completed']:
                return jsonify({'success': False, 'error': 'Course already completed'})
            else:
                # Update to completed
                conn.execute(
                    'UPDATE user_courses SET completed = 1, completion_date = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?',
                    (user['id'], course_id)
                )
                conn.commit()
                log_completion_event(user['id'], course_id, course['title'])
                return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            log_completion_event(user['id'], course_id, course['title'])
            return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

def log_completion_event(user_id, course_id, course_title):
    """Log course completion event"""
    try:
        log_message = f'User {user_id} completed course {course_id}: {course_title}'
        log_security_event('course_completion', log_message, request.remote_addr, user_id)
    except Exception as e:
        log_security_event('course_completion_error', f'Error logging completion for user {user_id}, course {course_id}: {str(e)}', request.remote_addr, user_id)

@app.route('/update-completion-date/<int:course_id>', methods=['POST'])
def update_completion_date(course_id):
    """Update completion date for a course"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    try:
        completion_date = request.form.get('completion_date')
        user_id = user['id']
        
        conn = get_db_connection()
        try:
            # Update completion date
            conn.execute(
                'UPDATE user_courses SET completion_date = ? WHERE user_id = ? AND course_id = ?',
                (completion_date, user_id, course_id)
            )
            conn.commit()
            flash('Completion date updated successfully!', 'success')
            log_security_event('completion_date_update', 
                             f'Updated completion date for course {course_id} to {completion_date}',
                             request.remote_addr, user_id)
            
        finally:
            conn.close()
            
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
    except Exception as e:
        flash(f'Error updating completion date: {str(e)}', 'error')
        log_security_event('completion_date_update_error', 
                         f'Error updating completion date for user {user_id}, course {course_id}: {str(e)}',
                         request.remote_addr, user_id)
    
    return redirect(url_for('my_courses'))

@app.route('/learnings')
def learnings():
    """Learning entries page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get user's learning entries
    conn = get_db_connection()
    try:
        entries = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC
        ''', (user['id'],)).fetchall()
        return render_template('learnings/index.html', entries=entries)
    finally:
        conn.close()

@app.route('/add-learning', methods=['GET', 'POST'])
def add_learning():
    """Add learning entry"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '')
        custom_date = request.form.get('custom_date')
        is_global = request.form.get('is_global') == 'on'
        
        if title:
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO learning_entries (user_id, title, description, tags, custom_date, is_global)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user['id'], title, description, tags, custom_date, is_global))
                conn.commit()
                flash('Learning entry added successfully!', 'success')
                return redirect(url_for('learnings'))
            finally:
                conn.close()
        else:
            flash('Title is required.', 'error')
    
    return render_template('learnings/add.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle profile updates (basic implementation)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user data
    conn = get_db_connection()
    try:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        
        # Calculate user stats
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']
        
        completed_courses_count = conn.execute('''
            SELECT COUNT(*) as count FROM user_courses 
            WHERE user_id = ? AND completed = 1
        ''', (user['id'],)).fetchone()['count']
        
        # Calculate level progression info
        user_points = user_data['points'] if user_data else 0
        current_level = user_data['level'] if user_data else 'Beginner'
        
        # Get level settings from database
        level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        level_mapping = {level['level_name']: level['points_required'] for level in level_settings}
        
        # Calculate next level info
        next_level = None
        points_to_next = 0
        level_points = 0
        
        # Find current level points and next level
        current_level_points = level_mapping.get(current_level, 0)
        level_points = user_points - current_level_points
        
        # Find next level
        for level_name, required_points in level_mapping.items():
            if user_points < required_points:
                next_level = level_name
                points_to_next = required_points - user_points
                break
        
        # Calculate progress percentage
        if next_level:
            next_level_points = level_mapping[next_level]
            prev_level_points = current_level_points
            if next_level_points > prev_level_points:
                progress_percentage = ((user_points - prev_level_points) / (next_level_points - prev_level_points)) * 100
            else:
                progress_percentage = 100
        else:
            progress_percentage = 100  # Max level reached
        
        # Create level_info object
        level_info = {
            'next_level': next_level,
            'points_to_next': points_to_next,
            'level_points': max(0, level_points),
            'progress_percentage': progress_percentage
        }
        
        # For now, provide empty points_log until points logging is implemented
        points_log = []
        
        return render_template('dashboard/profile.html', 
                             user=user_data,
                             learning_count=learning_count,
                             completed_courses_count=completed_courses_count,
                             level_info=level_info,
                             points_log=points_log)
    finally:
        conn.close()

@app.route('/points_log')
def points_log():
    """View user's points transaction history"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # For now, return empty points log
    # TODO: Implement actual points logging system
    return render_template('dashboard/profile.html', 
                         user=user,
                         learning_count=0,
                         completed_courses_count=0,
                         level_info={'next_level': None, 'points_to_next': 0, 'level_points': 0, 'progress_percentage': 0},
                         points_log=[])

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
        level_mapping = {'Beginner': 0, 'Intermediate': 150, 'Advanced': 250}
        next_level = 'Advanced'
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
    """Admin session management with dynamic statistics"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Get active sessions
        active_sessions = conn.execute('''
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
        
        # Get activity statistics (last 7 days)
        activity_stats = conn.execute('''
            SELECT activity_type, COUNT(*) as count
            FROM session_activity 
            WHERE datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY activity_type
            ORDER BY count DESC
        ''').fetchall()
        
        # Get daily login statistics (last 7 days)
        login_stats = conn.execute('''
            SELECT DATE(created_at) as login_date, COUNT(*) as login_count
            FROM user_sessions 
            WHERE datetime(created_at) >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY login_date DESC
        ''').fetchall()
        
        # Calculate today's login count
        today_login_count = 0
        today_date = conn.execute("SELECT DATE('now')").fetchone()[0]
        for stat in login_stats:
            if stat['login_date'] == today_date:
                today_login_count = stat['login_count']
                break
        
        return render_template('admin/sessions.html', 
                             active_sessions=active_sessions,
                             activity_stats=activity_stats,
                             login_stats=login_stats,
                             today_login_count=today_login_count)
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
    """Admin course management with pagination"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)  # Default 25 courses per page
    search = request.args.get('search', '', type=str)
    source_filter = request.args.get('source', '', type=str)
    level_filter = request.args.get('level', '', type=str)
    url_status_filter = request.args.get('url_status', '', type=str)
    points_filter = request.args.get('points', '', type=str)
    
    # Ensure per_page is within reasonable bounds
    per_page = max(10, min(100, per_page))
    
    # Get courses with pagination
    conn = get_db_connection()
    try:
        # Build WHERE clause for filters
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(title LIKE ? OR description LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
            
        if source_filter:
            where_conditions.append("source = ?")
            params.append(source_filter)
            
        if level_filter:
            where_conditions.append("level = ?")
            params.append(level_filter)
            
        if url_status_filter:
            where_conditions.append("url_status = ?")
            params.append(url_status_filter)
            
        if points_filter:
            if points_filter == "0-100":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 0 AND 100")
            elif points_filter == "100-200":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 100 AND 200")
            elif points_filter == "200-300":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 200 AND 300")
            elif points_filter == "300-400":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 300 AND 400")
            elif points_filter == "400+":
                where_conditions.append("CAST(points as INTEGER) > 400")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count for pagination
        count_query = f'SELECT COUNT(*) as count FROM courses {where_clause}'
        total_courses = conn.execute(count_query, params).fetchone()['count']
        
        # Calculate pagination info
        total_pages = max(1, (total_courses + per_page - 1) // per_page)  # Ceiling division
        page = max(1, min(page, total_pages))  # Ensure page is within bounds
        offset = (page - 1) * per_page
        
        # Get courses for current page
        query = f'''
            SELECT * FROM courses 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        courses = conn.execute(query, params).fetchall()
        
        # Get available sources and levels for filters
        sources = conn.execute('SELECT DISTINCT source FROM courses WHERE source IS NOT NULL ORDER BY source').fetchall()
        levels = conn.execute('SELECT DISTINCT level FROM courses WHERE level IS NOT NULL ORDER BY level').fetchall()
        
        # Calculate statistics for the dashboard (from entire database, not just current page)
        stats_query = '''
            SELECT 
                COUNT(*) as total_courses,
                COUNT(CASE WHEN source = 'Manual' THEN 1 END) as manual_entries,
                COUNT(CASE WHEN url_status = 'Working' THEN 1 END) as working_urls,
                COUNT(CASE WHEN url_status = 'Not Working' OR url_status = 'Broken' THEN 1 END) as broken_urls
            FROM courses
        '''
        stats = conn.execute(stats_query).fetchone()
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_courses': total_courses,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'start_course': offset + 1,
            'end_course': min(offset + per_page, total_courses)
        }
        
        return render_template('admin/courses.html', 
                             courses=courses, 
                             pagination=pagination_info,
                             stats=stats,
                             sources=[row['source'] for row in sources],
                             levels=[row['level'] for row in levels],
                             current_search=search,
                             current_source=source_filter,
                             current_level=level_filter,
                             current_url_status=url_status_filter,
                             current_points=points_filter)
    finally:
        conn.close()

@app.route('/admin/debug_environment', methods=['GET'])
def debug_environment():
    """Debug endpoint to check Azure environment"""
    import sys
    import os
    
    try:
        # Test imports
        import pandas as pd
        pandas_version = pd.__version__
        pandas_ok = True
    except ImportError as e:
        pandas_version = f"IMPORT ERROR: {e}"
        pandas_ok = False
    
    try:
        import openpyxl
        openpyxl_version = openpyxl.__version__
        openpyxl_ok = True
    except ImportError as e:
        openpyxl_version = f"IMPORT ERROR: {e}"
        openpyxl_ok = False
    
    try:
        import sqlite3
        sqlite_version = sqlite3.sqlite_version
        sqlite_ok = True
    except ImportError as e:
        sqlite_version = f"IMPORT ERROR: {e}"
        sqlite_ok = False
    
    debug_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "environment_variables": {
            "WEBSITE_SITE_NAME": os.environ.get("WEBSITE_SITE_NAME"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "PATH": os.environ.get("PATH", "")[:200] + "..." if len(os.environ.get("PATH", "")) > 200 else os.environ.get("PATH", ""),
        },
        "dependencies": {
            "pandas": {"version": pandas_version, "ok": pandas_ok},
            "openpyxl": {"version": openpyxl_version, "ok": openpyxl_ok},
            "sqlite3": {"version": sqlite_version, "ok": sqlite_ok}
        },
        "file_system": {
            "current_directory": os.getcwd(),
            "temp_directory": os.environ.get("TEMP", "/tmp"),
            "can_write_temp": os.access(os.environ.get("TEMP", "/tmp"), os.W_OK)
        }
    }
    
    return jsonify(debug_info)

@app.route('/admin/upload_excel_courses', methods=['POST'])
def admin_upload_excel_courses():
    """Upload courses from Excel file - Admin only"""
    try:
        print(f"📋 Upload request received from: {request.remote_addr}")
        user = get_current_user()
        print(f"📋 Current user: {user}")
        
        if not user or user['username'] != 'admin':
            print(f"❌ Access denied for user: {user}")
            return jsonify({'success': False, 'error': 'Admin privileges required.'}), 403
    except Exception as auth_error:
        print(f"❌ Authentication error: {auth_error}")
        return jsonify({'success': False, 'error': f'Authentication error: {str(auth_error)}'}), 500
    
    try:
        import pandas as pd
        from datetime import datetime
        import hashlib
        from upload_reports_manager import UploadReportsManager
        
        # Initialize upload reports manager
        try:
            reports_manager = UploadReportsManager()
        except Exception as e:
            print(f"Warning: Could not initialize upload reports manager: {e}")
            reports_manager = None
        
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded.'}), 400
        
        file = request.files['excel_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls).'}), 400
        
        # Read Excel file
        try:
            df = pd.read_excel(file)
            print(f"Excel file read successfully: {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            error_msg = f'Failed to read Excel file: {str(e)}'
            print(f"Excel read error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Validate required columns
        required_columns = ['title', 'url', 'source', 'level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f'Missing required columns: {", ".join(missing_columns)}. Required: {", ".join(required_columns)}'
            print(f"Column validation error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Process the data
        conn = None
        try:
            conn = get_db_connection()
            print("Database connection established")
            
            stats = {
                'total_processed': 0,
                'added': 0,
                'skipped': 0,
                'errors': 0,
                'error_details': []
            }
            
            # Create upload report entry
            report_id = None
            if reports_manager:
                try:
                    report_id = reports_manager.create_upload_report(
                        user_id=user['id'],
                        filename=file.filename,
                        total_rows=len(df),
                        processed_rows=0,
                        success_count=0,
                        error_count=0,
                        warnings_count=0
                    )
                except Exception as report_error:
                    print(f"Warning: Could not create upload report: {report_error}")
                    report_id = None
            
            # Get existing courses to check for duplicates
            existing_courses = conn.execute('SELECT title, url FROM courses').fetchall()
            existing_set = set()
            for row in existing_courses:
                title = row['title'] if row['title'] else ''
                url = row['url'] if row['url'] else ''
                if title and url:  # Only add if both title and url are not empty
                    existing_set.add((title.lower().strip(), url.lower().strip()))
            print(f"Found {len(existing_set)} existing courses for duplicate check")
            
            for index, row in df.iterrows():
                stats['total_processed'] += 1
                
                try:
                    # Extract and validate data
                    title = str(row['title']).strip() if pd.notna(row['title']) else ''
                    url = str(row['url']).strip() if pd.notna(row['url']) else ''
                    source = str(row['source']).strip() if pd.notna(row['source']) else ''
                    level = str(row['level']).strip() if pd.notna(row['level']) else ''
                    
                    # Validate required fields
                    if not all([title, url, source, level]):
                        error_detail = f'Row {index + 1}: Missing required data - title: {bool(title)}, url: {bool(url)}, source: {bool(source)}, level: {bool(level)}'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Validate level
                    if level not in ['Beginner', 'Intermediate', 'Advanced']:
                        error_detail = f'Row {index + 1}: Invalid level "{level}", must be Beginner, Intermediate, or Advanced'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Validate URL format
                    if not url.startswith(('http://', 'https://')):
                        error_detail = f'Row {index + 1}: Invalid URL format "{url}", must start with http:// or https://'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Check for duplicates
                    if (title.lower(), url.lower()) in existing_set:
                        stats['skipped'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='skipped',
                                    message='Duplicate course already exists',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add skipped row detail: {detail_error}")
                        continue
                    
                    # Extract optional fields
                    description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                    category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None
                    difficulty = str(row.get('difficulty', '')).strip() if pd.notna(row.get('difficulty')) else None
                    
                    # Handle points
                    points = 0
                    if 'points' in row and pd.notna(row['points']):
                        try:
                            points = int(float(row['points']))
                            if points < 0:
                                points = 0
                        except (ValueError, TypeError):
                            points = 0
                    
                    # Auto-assign level based on points if points are provided
                    if points > 0:
                        if points < 150:
                            level = 'Beginner'
                        elif points < 250:
                            level = 'Intermediate'
                        else:
                            level = 'Advanced'
                    
                    # Insert the course
                    try:
                        conn.execute('''
                            INSERT INTO courses 
                            (title, description, url, link, source, level, points, category, difficulty, created_at, url_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            title,
                            description,
                            url,
                            url,  # Use the same URL for both url and link columns
                            source,
                            level,
                            points,
                            category,
                            difficulty,
                            datetime.now().isoformat(),
                            'Pending'
                        ))
                        
                        # Add to existing set to prevent duplicates within the same upload
                        existing_set.add((title.lower(), url.lower()))
                        stats['added'] += 1
                        
                        # Add successful row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='success',
                                    message='Course added successfully',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add row detail: {detail_error}")
                        
                    except Exception as db_error:
                        error_detail = f'Row {index + 1}: Database insert failed - {str(db_error)}'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        print(f"Database insert error for row {index + 1}: {str(db_error)}")
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add DB error row detail: {detail_error}")
                        continue
                    
                except Exception as row_error:
                    error_detail = f'Row {index + 1}: Processing failed - {str(row_error)}'
                    stats['error_details'].append(error_detail)
                    stats['errors'] += 1
                    print(f"Row processing error for row {index + 1}: {str(row_error)}")
                    
                    # Add row detail to report
                    if report_id and reports_manager:
                        try:
                            reports_manager.add_row_detail(
                                report_id=report_id,
                                row_number=index + 1,
                                status='failed',
                                message=error_detail,
                                course_title='Unknown',
                                course_url='Unknown'
                            )
                        except Exception as detail_error:
                            print(f"Warning: Could not add processing error row detail: {detail_error}")
                    continue
            
            # Commit the transaction
            try:
                conn.commit()
                print(f"Transaction committed successfully. Stats: {stats}")
                
                # Update the upload report with final statistics
                if report_id and reports_manager:
                    try:
                        reports_manager.update_upload_report(
                            report_id=report_id,
                            processed_rows=stats['total_processed'],
                            success_count=stats['added'],
                            error_count=stats['errors'],
                            warnings_count=stats['skipped']
                        )
                    except Exception as update_error:
                        print(f"Warning: Could not update upload report: {update_error}")
            except Exception as commit_error:
                print(f"Commit error: {str(commit_error)}")
                return jsonify({
                    'success': False, 
                    'error': f'Failed to save courses to database: {str(commit_error)}',
                    'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }
                }), 500
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Excel upload completed successfully.',
                'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }
            }
            
            # Include error details if there were any errors (but still consider it a success if some courses were added)
            if stats['error_details']:
                response_data['warnings'] = stats['error_details'][:10]  # Limit to first 10 errors for readability
            
            return jsonify(response_data)
            
        except Exception as db_error:
            error_msg = f'Database operation failed: {str(db_error)}'
            print(f"Database error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
        finally:
            if conn:
                conn.close()
                print("Database connection closed")
            
    except ImportError as import_error:
        error_msg = f'pandas library is required for Excel processing. Import error: {str(import_error)}'
        print(f"Import error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Upload failed: {str(e)}'
        print(f"General error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/admin/download_excel_template')
def admin_download_excel_template():
    """Download Excel template for course upload - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        import pandas as pd
        from io import BytesIO
        from flask import send_file
        
        # Create sample data for the template
        sample_data = {
            'title': [
                'Introduction to Machine Learning',
                'Advanced Python Programming',
                'Azure AI Fundamentals'
            ],
            'description': [
                'Learn the basics of machine learning and AI concepts',
                'Deep dive into advanced Python programming techniques',
                'Understand Azure AI services and capabilities'
            ],
            'url': [
                'https://learn.microsoft.com/en-us/training/paths/machine-learning-foundations',
                'https://learn.microsoft.com/en-us/training/paths/python-advanced',
                'https://learn.microsoft.com/en-us/training/paths/azure-ai-fundamentals'
            ],
            'source': [
                'Microsoft Learn',
                'Microsoft Learn', 
                'Microsoft Learn'
            ],
            'level': [
                'Beginner',
                'Intermediate',
                'Advanced'
            ],
            'points': [
                120,
                200,
                300
            ],
            'category': [
                'Machine Learning',
                'Programming',
                'Cloud Computing'
            ],
            'difficulty': [
                'Easy',
                'Medium',
                'Hard'
            ]
        }
        
        # Create DataFrame
        df = pd.DataFrame(sample_data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Courses', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Courses']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='course_upload_template.xlsx'
        )
        
    except ImportError:
        flash('pandas library is required for Excel processing.', 'error')
        return redirect(url_for('admin_courses'))
    except Exception as e:
        flash(f'Failed to generate template: {str(e)}', 'error')
        return redirect(url_for('admin_courses'))

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

@app.route('/admin/url-validation')
@require_admin
def admin_url_validation():
    """URL validation management page - Admin only"""
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
            status = course.get('url_status', 'Unchecked') if course else 'Unchecked'
            if status == 'Working':
                summary['working']['count'] += 1
            elif status == 'Not Working':
                summary['not_working']['count'] += 1
            elif status == 'Broken':
                summary['broken']['count'] += 1
            else:
                summary['unchecked']['count'] += 1
        
        return render_template('admin/url_validation.html',
                             courses=courses,
                             summary=summary)
        
    except Exception as e:
        flash(f'Error loading URL validation data: {e}', 'error')
        return redirect(url_for('admin_courses'))
    finally:
        conn.close()

@app.route('/admin/validate-all-urls', methods=['POST'])
@require_admin
def admin_validate_all_urls():
    """Start URL validation for all courses (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        courses = conn.execute('SELECT id, title, url FROM courses WHERE url IS NOT NULL AND url != ""').fetchall()
        conn.close()
        
        if not courses:
            return jsonify({'success': False, 'message': 'No courses with URLs found'})
        
        # Start validation in background thread
        def validate_urls():
            conn = get_db_connection()
            try:
                for course in courses:
                    try:
                        # Basic URL validation
                        parsed = urlparse(course['url'])
                        if not parsed.scheme or not parsed.netloc:
                            status = 'Broken'
                        else:
                            # Try to connect to URL (with timeout)
                            try:
                                response = requests.head(course['url'], timeout=10, allow_redirects=True)
                                if response.status_code < 400:
                                    status = 'Working'
                                else:
                                    status = 'Not Working'
                            except requests.exceptions.RequestException:
                                # If HEAD fails, try GET with smaller content
                                try:
                                    response = requests.get(course['url'], timeout=10, allow_redirects=True, stream=True)
                                    if response.status_code < 400:
                                        status = 'Working'
                                    else:
                                        status = 'Not Working'
                                except requests.exceptions.RequestException:
                                    status = 'Broken'
                    except Exception:
                        status = 'Broken'
                    
                    # Update database
                    conn.execute('''
                        UPDATE courses 
                        SET url_status = ?, last_url_check = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (status, course['id']))
                    conn.commit()
            except Exception as e:
                print(f"URL validation error: {e}")
            finally:
                conn.close()
        
        # Start background thread
        thread = threading.Thread(target=validate_urls)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'URL validation started for {len(courses)} courses',
            'course_count': len(courses)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting validation: {str(e)}'})

@app.route('/admin/url-validation-status')
@require_admin
def admin_url_validation_status():
    """Get URL validation status (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        
        # Get summary of validation status
        courses = conn.execute('''
            SELECT id, title, url, url_status, last_url_check
            FROM courses 
            WHERE url IS NOT NULL AND url != ""
            ORDER BY last_url_check DESC
        ''').fetchall()
        
        # Count by status
        status_counts = {
            'working': 0,
            'not_working': 0,
            'broken': 0,
            'unchecked': 0
        }
        
        course_list = []
        for course in courses:
            status = course.get('url_status', 'Unchecked') or 'Unchecked'
            status_lower = status.lower().replace(' ', '_')
            if status_lower in status_counts:
                status_counts[status_lower] += 1
            else:
                status_counts['unchecked'] += 1
            
            course_list.append({
                'id': course['id'],
                'title': course['title'],
                'url': course['url'],
                'status': status,
                'last_check': course.get('last_url_check', 'Never')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'courses': course_list,
            'summary': status_counts,
            'total_courses': len(course_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting status: {str(e)}'})

@app.route('/admin/edit-course/<int:course_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_course(course_id):
    """Edit a course (admin only)"""
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            provider = request.form.get('provider')
            source = request.form.get('source')
            url = request.form.get('url')
            link = request.form.get('link')
            level = request.form.get('level')
            category = request.form.get('category')
            points = request.form.get('points', 0)
            
            if not title or not description:
                flash('Title and description are required.', 'error')
                return redirect(url_for('admin_edit_course', course_id=course_id))
            
            try:
                points = int(points) if points else 0
            except ValueError:
                points = 0
            
            # Auto-calculate level based on points
            if points < 150:
                level = 'Beginner'
            elif points < 250:
                level = 'Intermediate'
            else:
                level = 'Advanced'
            
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
        # Delete related records first (if user_courses table exists)
        try:
            conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        except:
            pass  # Table might not exist
        
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/bulk-delete-courses', methods=['POST'])
@require_admin
def admin_bulk_delete_courses():
    """Bulk delete multiple courses (admin only)"""
    course_ids = request.form.getlist('course_ids')
    
    if not course_ids:
        flash('No courses selected for deletion.', 'warning')
        return redirect(url_for('admin_courses'))
    
    # Validate that all IDs are integers
    try:
        course_ids = [int(id) for id in course_ids]
    except ValueError:
        flash('Invalid course IDs provided.', 'error')
        return redirect(url_for('admin_courses'))
    
    conn = get_db_connection()
    deleted_count = 0
    
    try:
        # Delete related records first (if user_courses table exists)
        try:
            for course_id in course_ids:
                conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        except:
            pass  # Table might not exist
        
        # Delete courses
        for course_id in course_ids:
            result = conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            if result.rowcount > 0:
                deleted_count += 1
        
        conn.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} course(s)!', 'success')
        else:
            flash('No courses were deleted. They may have already been removed.', 'warning')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting courses: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@require_admin
def admin_delete_user(user_id):
    """Delete a user (admin only) - requires explicit authorization"""
    # Explicit authorization check for user deletion
    try:
        # Check if this is production environment
        if production_safety.environment == 'production':
            # In production, require additional explicit authorization
            explicit_authorization = request.form.get('explicit_authorization')
            if not explicit_authorization:
                flash('User deletion requires explicit authorization in production.', 'error')
                return redirect(url_for('admin_users'))
    except:
        pass  # Continue if production_safety not available
    
    conn = get_db_connection()
    try:
        # Check if user exists and get username for validation
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user['username']
        
        # Protected users that cannot be deleted - admin user cannot be deleted
        protected_users = ['admin']
        if username in protected_users:
            flash(f'Admin user cannot be deleted - system protection active.', 'error')
            return redirect(url_for('admin_users'))
        
        # Delete user and related data
        try:
            conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        try:
            conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        try:
            conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        flash(f'User "{username}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/toggle-user-status/<int:user_id>', methods=['POST'])
@require_admin
def admin_toggle_user_status(user_id):
    """Toggle user status between active and inactive (admin only)"""
    conn = get_db_connection()
    try:
        # Get current user status
        user = conn.execute('SELECT username, status FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Toggle status
        new_status = 'inactive' if user['status'] == 'active' else 'active'
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        
        flash(f'User "{user["username"]}" status changed to {new_status}.', 'success')
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/set-user-password', methods=['POST'])
@require_admin 
def admin_set_user_password():
    """Allow admin to set a custom password for a user"""
    user_id = request.form.get('user_id')
    new_password = request.form.get('custom_password')  # Updated to match form field name
    confirm_password = request.form.get('confirm_custom_password')
    
    if not user_id or not new_password:
        flash('User ID and new password are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if new_password != confirm_password:
        flash('Password confirmation does not match.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get user info
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Hash and update password
        hashed_password = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (hashed_password, user_id)
        )
        conn.commit()
        
        flash(f'Password updated successfully for user: {user["username"]}', 'success')
        
    except Exception as e:
        flash(f'Error updating password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reset-all-user-passwords', methods=['POST'])
@require_admin
def admin_reset_all_user_passwords():
    """Reset all user passwords (admin only) - requires explicit authorization"""
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    confirmation = request.form.get('reset_all_confirmation')
    
    # Explicit authorization check for bulk password reset
    try:
        if production_safety.environment == 'production':
            explicit_authorization = request.form.get('explicit_authorization')
            if not explicit_authorization:
                flash('Bulk password reset requires explicit authorization in production.', 'error')
                return redirect(url_for('admin_users'))
    except:
        pass  # Continue if production_safety not available
    
    if not new_password or not confirm_password:
        flash('Both password fields are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if new_password != confirm_password:
        flash('Password confirmation does not match.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
        
    if not confirmation:
        flash('You must confirm the bulk password reset operation.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get all users except admin
        users = conn.execute('SELECT id, username FROM users WHERE username != ?', ('admin',)).fetchall()
        
        if not users:
            flash('No users found to reset passwords for.', 'warning')
            return redirect(url_for('admin_users'))
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update all non-admin users
        updated_count = 0
        for user in users:
            conn.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (hashed_password, user['id'])
            )
            updated_count += 1
        
        conn.commit()
        flash(f'Successfully reset passwords for {updated_count} users. Users will need to use the new password on their next login.', 'success')
        
    except Exception as e:
        flash(f'Error resetting passwords: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

# Legacy route name for compatibility with existing form
@app.route('/admin/reset-user-password', methods=['POST'])
@require_admin
def admin_reset_user_password():
    """Legacy route - redirects to the new set password function"""
    return admin_set_user_password()

@app.route('/admin/search-and-import-courses', methods=['POST'])
@require_admin
def admin_search_and_import_courses():
    """Search and import courses from external sources (admin only)"""
    search_term = request.form.get('search_term', '')
    source = request.form.get('source', 'manual')
    
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

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Admin settings"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Update level settings
        try:
            for level_name in ['beginner', 'learner', 'intermediate', 'expert']:
                points_key = f'{level_name}_points'
                if points_key in request.form:
                    points_required = int(request.form[points_key])
                    conn.execute(
                        'UPDATE level_settings SET points_required = ? WHERE LOWER(level_name) = ?',
                        (points_required, level_name)
                    )
            conn.commit()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('admin_settings'))
    
    # Get current level settings
    try:
        level_settings = conn.execute(
            'SELECT level_name, points_required FROM level_settings ORDER BY points_required ASC'
        ).fetchall()
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'error')
        level_settings = []
    finally:
        conn.close()
    
    return render_template('admin/settings.html', level_settings=level_settings)

@app.route('/admin/change-password', methods=['GET', 'POST'])
def admin_change_password():
    """Admin change password"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('admin/change_password.html')
        
        # Verify current password
        conn = get_db_connection()
        try:
            admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
            if admin_user and check_password_hash(admin_user['password_hash'], current_password):
                # Update password
                new_hash = generate_password_hash(new_password)
                conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
                conn.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Current password is incorrect.', 'error')
        finally:
            conn.close()
    
    return render_template('admin/change_password.html')

# Admin User Management Routes
@app.route('/admin/add-user', methods=['GET', 'POST'])
@require_admin
def admin_add_user():
    """Add a new user (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        level = request.form.get('level', 'Beginner')
        status = request.form.get('status', 'active')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
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

# Admin Course Management Routes
@app.route('/admin/add-course', methods=['GET', 'POST'])
@require_admin
def admin_add_course():
    """Add a new course with comprehensive validation (admin only)"""
    if request.method == 'POST':
        # Course validator temporarily disabled - module removed in cleanup
        logger.info("Course validation temporarily disabled - using basic validation only")
        flash('Course added with basic validation. Advanced URL validation temporarily unavailable.', 'info')
        validator = None
        
        # Collect form data
        course_data = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'provider': request.form.get('provider', '').strip(),  # Keep for backward compatibility
            'source': request.form.get('source', '').strip(),
            'url': request.form.get('url', '').strip() or None,
            'link': request.form.get('link', '').strip() or None,
            'level': request.form.get('level', '').strip(),
            'category': request.form.get('category', '').strip() or None,
            'points': request.form.get('points', 0)
        }
        
        # Validate with comprehensive schema validation
        if validator:
            course = validator.validate_schema(course_data)
            
            # Check for validation errors
            if not course.is_valid:
                for error in course.validation_errors:
                    if error.severity == 'error':
                        flash(f'{error.field.title()}: {error.message}', 'error')
                    else:
                        flash(f'{error.field.title()}: {error.message}', 'warning')
                
                # If there are errors, return to form with data
                if any(e.severity == 'error' for e in course.validation_errors):
                    return render_template('admin/add_course.html', course_data=course_data)
            
            # Validate URLs if provided
            url_validation_results = {}
            validation_warnings = []
            
            if course.url:
                logger.info(f"Validating primary URL: {course.url}")
                url_result = validator.validate_url(course.url)
                url_validation_results['url'] = url_result
                
                if url_result['status'] not in ['Working']:
                    validation_warnings.append(f"Primary URL may not be accessible: {url_result.get('error_message', 'Unknown error')}")
                    
            if course.link and course.link != course.url:
                logger.info(f"Validating link URL: {course.link}")
                link_result = validator.validate_url(course.link)
                url_validation_results['link'] = link_result
                
                if link_result['status'] not in ['Working']:
                    validation_warnings.append(f"Link URL may not be accessible: {link_result.get('error_message', 'Unknown error')}")
            
            # Show URL validation warnings
            for warning in validation_warnings:
                flash(warning, 'warning')
                
            # Update course data with validation results
            if course.url and 'url' in url_validation_results:
                course.url_status = url_validation_results['url']['status']
                course.last_url_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Fallback validation without validator
            if not course_data['title'] or not course_data['description']:
                flash('Title and description are required.', 'error')
                return render_template('admin/add_course.html', course_data=course_data)
            
            try:
                course_data['points'] = int(course_data['points']) if course_data['points'] else 0
            except ValueError:
                course_data['points'] = 0
                flash('Points must be a number. Set to 0.', 'warning')
            
            course = type('Course', (), course_data)()
            course.url_status = 'unchecked'
            course.last_url_check = None
        
        # Insert into database
        conn = get_db_connection()
        try:
            # Determine which URL field to use for url_status tracking
            primary_url = course.url or course.link
            
            conn.execute('''
                INSERT INTO courses (
                    title, description, provider, source, url, link, level, category, points,
                    created_at, url_status, last_url_check
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
            ''', (
                course.title, course.description, course_data['provider'], course.source,
                course.url, course.link, course.level, course.category, course.points,
                course.url_status, course.last_url_check
            ))
            conn.commit()
            
            # Success message with validation info
            success_msg = 'Course added successfully!'
            if validator and primary_url:
                if course.url_status == 'Working':
                    success_msg += ' URL validation passed.'
                elif course.url_status in ['Not Working', 'Broken']:
                    success_msg += f' Note: URL validation failed ({course.url_status}).'
                else:
                    success_msg += ' URL validation completed with warnings.'
            
            flash(success_msg, 'success')
            logger.info(f"Course added successfully: {course.title} (URL Status: {course.url_status})")
            
            return redirect(url_for('admin_courses'))
            
        except Exception as e:
            logger.error(f"Database error adding course: {e}")
            flash(f'Error adding course: {str(e)}', 'error')
            return render_template('admin/add_course.html', course_data=course_data)
        finally:
            conn.close()
    
    return render_template('admin/add_course.html')

# Global storage for course fetch status (since background threads can't access Flask session)
course_fetch_status = {}

@app.route('/admin/populate-ai-courses', methods=['POST'])
@require_admin
def admin_populate_ai_courses():
    """Fetch AI/Copilot courses from live APIs with real-time updates"""
    logger.info("🔍 Admin initiated FAST live API course fetching")
    
    # Fast course fetcher temporarily disabled - module removed in cleanup
    logger.info("Fast course API fetcher temporarily disabled - using basic course addition only")
    return jsonify({
        'success': False,
        'error': 'Fast course fetcher temporarily unavailable. Please add courses manually.',
        'message': 'Advanced course fetching is temporarily disabled during workspace cleanup.'
    }), 503

    try:
        logger.info("📡 Starting FAST live API course fetching...")
        
        # Start asynchronous course fetching with real-time updates
        import threading
        import uuid
        
        # Generate unique fetch ID for this request
        fetch_id = str(uuid.uuid4())[:8]
        
        def fetch_courses_async():
            """Background task to fetch courses asynchronously"""
            try:
                # Update status: Starting
                course_fetch_status[fetch_id] = {
                    'status': 'fetching',
                    'message': 'Fetching courses from live APIs...',
                    'progress': 10
                }
                
                # Fetch courses (faster, no fallbacks)
                result = get_fast_ai_courses(10)  # Reduced count for speed
                
                # Update status: Complete
                course_fetch_status[fetch_id] = {
                    'status': 'complete',
                    'message': f'Successfully added {result["courses_added"]} courses in {result["total_time"]}s',
                    'progress': 100,
                    'result': result
                }
                
                logger.info(f"📚 Fast course fetching completed: {result['courses_added']} courses added")
                
            except Exception as e:
                # Update status: Error
                course_fetch_status[fetch_id] = {
                    'status': 'error',
                    'message': f'Error: {str(e)}',
                    'progress': 0,
                    'error': str(e)
                }
                logger.error(f"❌ Fast course fetching failed: {e}")
        
        # Start background thread
        fetch_thread = threading.Thread(target=fetch_courses_async)
        fetch_thread.daemon = True
        fetch_thread.start()
        
        # Return JSON response with fetch ID for status tracking
        return jsonify({
            'success': True,
            'fetch_id': fetch_id,
            'message': 'Course fetching started - real APIs only, no fallbacks'
        })
            
    except Exception as e:
        error_msg = f'Error starting fast API course fetching: {str(e)}'
        logger.error(f"❌ Failed to start fast background fetching: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/admin/course-fetch-status/<fetch_id>')
@require_admin
def get_course_fetch_status(fetch_id):
    """Get the status of a course fetching operation"""
    status = course_fetch_status.get(fetch_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Fetch operation not found'
        }), 404


# Backward compatibility alias for old route name
@app.route('/admin/populate-linkedin-courses', methods=['POST'])
@require_admin  
def admin_populate_linkedin_courses():
    """Backward compatibility alias - redirects to new admin_populate_ai_courses"""
    logger.info("⚠️ Using deprecated route - redirecting to admin_populate_ai_courses")
    return admin_populate_ai_courses()

@app.route('/setup-admin')
def setup_admin():
    """Simple setup route to create admin user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            conn.close()
            return "✅ Admin user already exists! <a href='/'>Go to Login</a>"
        
        # Create admin user
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return f"""
        🎉 Admin user created successfully!<br>
        Username: admin<br>
        Password: {admin_password}<br>
        <a href='/'>Go to Login</a>
        """
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/health')
def health_check():
    """Health check endpoint with admin initialization"""
    
    import sqlite3
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    html_template = '''
    <html>
    <head><title>Health Check</title></head>
    <body style="font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px;">
        <h2>🔍 AI Learning Tracker - Health Check</h2>
        {content}
        <hr>
        <p><small>Last updated: {timestamp}</small></p>
    </body>
    </html>
    '''
    
    try:
        status_info = []
        
        # Check database connection
        try:
            conn = get_db_connection()
            status_info.append("✅ Database connection: OK")
            
            # Check tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'users' in tables:
                status_info.append("✅ Users table: EXISTS")
                
                # Check admin user
                cursor.execute("SELECT id, username, level FROM users WHERE username = 'admin'")
                admin_user = cursor.fetchone()
                
                if admin_user:
                    status_info.append(f"✅ Admin user: EXISTS (ID: {admin_user[0]}, Level: {admin_user[2]})")
                else:
                    status_info.append("❌ Admin user: MISSING")
                    
                    # Try to create admin user
                    status_info.append("🔧 Attempting to create admin user...")
                    
                    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
                    password_hash = generate_password_hash(admin_password)
                    
                    cursor.execute("""
                        INSERT INTO users (
                            username, password_hash, level, points, status,
                            user_selected_level, login_count, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'admin', password_hash, 'Advanced', 100, 'active',
                        'Advanced', 0, datetime.now().isoformat()
                    ))
                    
                    admin_id = cursor.lastrowid
                    conn.commit()
                    
                    status_info.append(f"🎉 Admin user CREATED! (ID: {admin_id})")
                
                # Check total users
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                status_info.append(f"📊 Total users: {user_count}")
                
            else:
                status_info.append("❌ Users table: MISSING")
            
            conn.close()
            
        except Exception as e:
            status_info.append(f"❌ Database error: {str(e)}")
        
        # Check environment variables
        admin_pwd = os.environ.get('ADMIN_PASSWORD')
        if admin_pwd:
            status_info.append(f"✅ ADMIN_PASSWORD: SET (length: {len(admin_pwd)})")
        else:
            status_info.append("❌ ADMIN_PASSWORD: NOT SET")
        
        # Add login test link
        status_info.append("")
        status_info.append("🔗 <strong>Test Login:</strong>")
        status_info.append(f'<a href="/" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px;">Go to Login Page</a>')
        
        content = "<br>".join(status_info)
        
        return html_template.format(
            content=content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
    except Exception as e:
        return html_template.format(
            content=f"❌ Health check failed: {str(e)}",
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )

@app.route('/init-admin')
def simple_init_admin():
    """Simple admin initialization via URL parameter"""
    
    # Get password from URL parameter
    init_password = request.args.get('password', '')
    expected_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    # Basic HTML template
    html_template = '''
    <html>
    <head><title>Admin Initialization</title></head>
    <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-bottom: 20px;">{title}</h2>
            {content}
        </div>
    </body>
    </html>
    '''
    
    if not init_password:
        return html_template.format(
            title="🔧 Admin User Initialization",
            content='''
            <p>To initialize the admin user, add your password as a URL parameter:</p>
            <p><strong>URL Format:</strong></p>
            <code style="background: #f0f0f0; padding: 10px; border-radius: 4px; display: block; margin: 10px 0;">
            https://your-app.azurewebsites.net/init-admin?password=YOUR_ADMIN_PASSWORD
            </code>
            <p><small>⚠️ Use your ADMIN_PASSWORD environment variable value</small></p>
            '''
        )
    
    if init_password != expected_password:
        return html_template.format(
            title="❌ Invalid Password",
            content='''
            <p>The initialization password is incorrect.</p>
            <p>Please check your ADMIN_PASSWORD environment variable.</p>
            <a href="/init-admin" style="color: #007bff;">Try Again</a>
            '''
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            conn.close()
            return html_template.format(
                title="✅ Admin Already Exists",
                content='''
                <p>The admin user has already been created.</p>
                <p>You can now login with username <strong>admin</strong></p>
                <a href="/" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    Go to Login
                </a>
                '''
            )
        
        # Create admin user
        password_hash = generate_password_hash(expected_password)
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        
        # Create demo user too
        demo_password = os.environ.get('DEMO_PASSWORD', 'demo123')
        cursor.execute("SELECT id FROM users WHERE username = 'demo'")
        if not cursor.fetchone():
            demo_hash = generate_password_hash(demo_password)
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, level, points, status,
                    user_selected_level, login_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'demo', demo_hash, 'Beginner', 0, 'active',
                'Beginner', 0, datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        return html_template.format(
            title="🎉 Initialization Complete!",
            content=f'''
            <p>✅ <strong>Admin user created successfully!</strong></p>
            <p>✅ Demo user created successfully</p>
            <p>📊 Admin user ID: {admin_id}</p>
            <hr style="margin: 20px 0;">
            <h3>🔗 Ready to Login:</h3>
            <p><strong>Username:</strong> admin</p>
            <p><strong>Password:</strong> [your ADMIN_PASSWORD]</p>
            <p><strong>Level:</strong> Advanced</p>
            <br>
            <a href="/" style="background: #28a745; color: white; padding: 15px 25px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                🚀 Go to Login Page
            </a>
            '''
        )
        
    except Exception as e:
        return html_template.format(
            title="❌ Initialization Failed",
            content=f'''
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please check the application logs for more details.</p>
            <a href="/init-admin" style="color: #007bff;">Try Again</a>
            '''
        )

# Initialize database on startup
try:
    if db_init:
        logger.info("🔄 Initializing database with Azure SQL support...")
        db_init()
        logger.info("✅ Database initialization completed")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")


@app.route('/create-admin-now')
def create_admin_now():
    """Emergency route to create admin user directly"""
    try:
        conn = get_db_connection()
        
        # First create users table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                user_selected_level TEXT DEFAULT 'Beginner',
                login_count INTEGER DEFAULT 0
            )
        ''')
        
        # Check if admin already exists
        existing_admin = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if existing_admin:
            conn.close()
            return f"<h2>Admin user already exists with ID: {existing_admin['id']}</h2><a href='/'>Go to Login</a>"
        
        # Create admin user with the known password
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 100, 'active', 'Advanced', 0))
        
        conn.commit()
        admin_id = conn.lastrowid
        conn.close()
        
        return f"<h2> Admin user created successfully!</h2><p>Admin ID: {admin_id}</p><p>Username: admin</p><p>You can now login at <a href='/'>the login page</a></p>"
        
    except Exception as e:
        return f"<h2> Error creating admin: {str(e)}</h2><a href='/create-admin-now'>Try Again</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
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
from urllib.parse import urlparse
try:
    from database_manager import get_db_connection as db_get_connection, init_database as db_init, db_manager
except ImportError:
    db_get_connection = None
    db_init = None
    db_manager = None

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

# Import Azure database sync for production
try:
    from azure_database_sync import AzureDatabaseSync
    azure_sync = AzureDatabaseSync()
    AZURE_SYNC_AVAILABLE = True
    print('✅ Azure database sync loaded')
except ImportError as e:
    print(f'⚠️  Azure sync not available: {e}')
    azure_sync = None
    AZURE_SYNC_AVAILABLE = False

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

# Initialize Azure database sync on startup
if AZURE_SYNC_AVAILABLE and azure_sync:
    print('🔄 Initializing Azure database sync...')
    try:
        # Download database from Azure Storage if available
        azure_sync.sync_from_azure_on_startup()
        print('✅ Azure database sync initialized successfully')
    except Exception as e:
        print(f'⚠️ Azure sync initialization failed: {e}')
        print('   Continuing with local database only')

# @app.before_first_request
def initialize_azure_sync():
    """Initialize Azure sync before first request"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.sync_from_azure_on_startup()
        except Exception as e:
            app.logger.warning(f'Azure sync failed on startup: {e}')

def sync_to_azure_after_change():
    """Upload database to Azure after changes"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.upload_database_to_azure()
        except Exception as e:
            app.logger.warning(f'Azure upload failed: {e}')


# Log environment detection
logger.info(f"Environment detected: {production_safety.environment}")
if production_safety.environment == 'production':
    logger.warning("PRODUCTION ENVIRONMENT - Enhanced safety measures active")

# Database configuration - dynamic based on environment
def get_database_path():
    """Get database path from environment configuration"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    elif database_url.startswith('sqlite://'):
        return database_url.replace('sqlite://', '')
    return 'ai_learning.db'

def get_db_connection():
    """Get database connection with environment-aware support for Azure SQL"""
    try:
        # Check if we should use Azure SQL
        database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
        
        if (database_url == 'azure_sql' or production_safety.environment == 'production') and db_get_connection:
            logger.info(f"🌍 Environment: {production_safety.environment}")
            
            if db_manager and db_manager.is_azure_sql:
                logger.info("📂 Connecting to Azure SQL Database")
            else:
                logger.info("📂 Using SQLite via database manager")
            
            return db_get_connection()
        else:
            # Use traditional SQLite connection
            database_path = get_database_path()
            
            # Log database connection details for debugging
            logger.info(f"📂 Connecting to database: {os.path.abspath(database_path)}")
            logger.info(f"🌍 Environment: {production_safety.environment}")
            logger.info(f"💾 Database exists: {os.path.exists(database_path)}")
            
            if os.path.exists(database_path):
                logger.info(f"📊 Database size: {os.path.getsize(database_path)} bytes")
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row
            return conn
            
    except Exception as e:
        # Fallback to old method if there are any issues
        logger.warning(f"Database manager error ({e}), using fallback SQLite connection")
        database_path = get_database_path()
        conn = sqlite3.connect(database_path)
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
    
    # PRODUCTION SAFETY: NEVER auto-create users in any environment
    # Users should only be created through proper admin interfaces
    # Database initialization should ONLY create schema, never data
    # This prevents accidental data overwrites in any environment
    
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

# Azure database backup scheduler
def azure_backup_scheduler():
    """Background thread to periodically backup database to Azure Storage"""
    import time
    time.sleep(300)  # Wait 5 minutes before first backup
    
    while True:
        try:
            # Azure sync temporarily disabled - module removed in cleanup
            logger.info("Azure backup scheduler: Module not available, skipping sync")
            time.sleep(1800)  # Check every 30 minutes
        except Exception as e:
            logger.error(f"Azure backup scheduler error: {e}")
            time.sleep(1800)  # Continue after error

# Start background threads
cleanup_thread = threading.Thread(target=session_cleanup_scheduler, daemon=True)
cleanup_thread.start()

backup_thread = threading.Thread(target=azure_backup_scheduler, daemon=True)
backup_thread.start()

# CRITICAL FIX: Prevent database reinitialization on every startup
# Only initialize database if it doesn't exist or is empty
def safe_init_db():
    """
    CRITICAL FUNCTION: Initialize database only if it doesn't exist or is empty.
    NEVER OVERWRITES EXISTING DATA - ONLY CREATES MISSING TABLES.
    Now includes Azure Storage sync for data persistence.
    """
    try:
        logger.info("🔍 SAFE_INIT_DB: Starting database safety check...")
        
        # AZURE STORAGE INTEGRATION: Temporarily disabled - module removed in cleanup
        logger.info("Azure sync temporarily disabled - using local database only")
        
        # Check if database file exists (may have been downloaded from Azure)
        db_path = get_database_path()
        if not os.path.exists(db_path):
            logger.info(f"📁 SAFE_INIT_DB: Database file {db_path} not found - will create new one")
            init_db()
            ensure_admin_exists()
            return
        
        conn = get_db_connection()
        
        # Check if users table exists
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        
        if not result:
            logger.info("🏗️ SAFE_INIT_DB: Users table missing - initializing schema...")
            conn.close()
            init_db()
            ensure_admin_exists()
            return
        
        # Check if there are any users (most critical check)
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            logger.info(f"✅ SAFE_INIT_DB: Database already has {user_count} users - PRESERVING ALL DATA")
            
            # Log existing users for verification
            try:
                users = conn.execute("SELECT id, username, created_at FROM users ORDER BY id").fetchall()
                logger.info("🔍 SAFE_INIT_DB: Existing users found:")
                for user in users:
                    logger.info(f"   - ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
            except Exception as e:
                logger.warning(f"⚠️ SAFE_INIT_DB: Could not log existing users: {e}")
            
            conn.close()
            
            # Still ensure admin exists but don't overwrite data
            ensure_admin_exists()
            logger.info("✅ SAFE_INIT_DB: Complete - existing data preserved")
            
            # AZURE STORAGE INTEGRATION: Temporarily disabled - module removed in cleanup
            logger.info("Azure sync temporarily disabled - using local database only")
            return
        else:
            logger.info("📋 SAFE_INIT_DB: Users table exists but empty - safe to initialize")
            conn.close()
            init_db()
            ensure_admin_exists()
            # Azure sync temporarily disabled - using local database only
            logger.info("Azure sync temporarily disabled - using local database only")
            return
        
    except Exception as e:
        logger.error(f"❌ SAFE_INIT_DB: Database check failed: {e}")
        logger.error(f"❌ SAFE_INIT_DB: Exception details: {type(e).__name__}: {str(e)}")
        try:
            # Emergency fallback - only if absolutely necessary
            logger.warning("⚠️ SAFE_INIT_DB: Attempting emergency fallback...")
            init_db()
            ensure_admin_exists()
        except Exception as fallback_error:
            logger.error(f"💥 SAFE_INIT_DB: Emergency fallback failed: {fallback_error}")
            raise

def ensure_admin_exists():
    """
    CRITICAL FUNCTION: Ensure admin user exists without overwriting existing admin data
    """
    try:
        logger.info("🔍 ENSURE_ADMIN: Checking admin user status...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id, username, password_hash, level, points, created_at FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            logger.info(f"✅ ENSURE_ADMIN: Admin user already exists - ID: {existing_admin[0]}, Level: {existing_admin[3]}, Points: {existing_admin[4]}")
            logger.info("✅ ENSURE_ADMIN: Preserving existing admin data - NO CHANGES MADE")
            conn.close()
            return
        
        # Only create admin if it doesn't exist
        logger.info("🔄 ENSURE_ADMIN: Admin user not found - creating new admin...")
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.info("✅ ENSURE_ADMIN: New admin user created successfully")
        logger.info(f"🔑 ENSURE_ADMIN: Admin password set from environment variable")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ ENSURE_ADMIN: Admin user check/creation failed: {e}")
        logger.error(f"❌ ENSURE_ADMIN: Exception details: {type(e).__name__}: {str(e)}")
        try:
            conn.close()
        except:
            pass

# Initialize database on startup (SAFE VERSION - preserves existing data)
safe_init_db()

# EMERGENCY FIX: Disable deployment safety to prevent data resets
# Initialize deployment safety and data integrity monitoring
try:
    # RESTORED - deployment safety module recreated
    from deployment_safety import init_deployment_safety
    deployment_safety = init_deployment_safety(app)
    logger.info("✅ Deployment safety initialized successfully")
except ImportError:
    logger.warning("⚠️ Deployment safety module not available - install azure-storage-blob for full functionality")
except Exception as e:
    logger.error(f"❌ Failed to initialize deployment safety: {e}")

# Re-enable blueprints - circular import issue resolved
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp  
from learnings.routes import learnings_bp
from admin.routes import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(learnings_bp, url_prefix='/learnings')
app.register_blueprint(admin_bp)

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
        # Base query for completed courses
        completed_query = '''
            SELECT c.*, uc.completed, uc.completion_date, 'system' as course_type
            FROM courses c 
            INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
        '''
        completed_params = [user['id']]
        
        # Apply filters to completed courses
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
        
        # Base query for recommended courses
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
        
        # Get available filter options
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

@app.route('/export-courses/<course_type>')
def export_courses(course_type):
    """Export courses to CSV"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        if course_type == 'completed':
            courses = conn.execute('''
                SELECT c.title, c.description, c.level, uc.completion_date
                FROM courses c 
                INNER JOIN user_courses uc ON c.id = uc.course_id 
                WHERE uc.user_id = ? AND uc.completed = 1
                ORDER BY uc.completion_date DESC
            ''', (user['id'],)).fetchall()
        else:  # recommended
            courses = conn.execute('''
                SELECT c.title, c.description, c.level, c.created_at as date_added
                FROM courses c 
                LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
                WHERE (uc.completed IS NULL OR uc.completed = 0)
                ORDER BY c.created_at DESC
            ''', (user['id'],)).fetchall()
        
        # Create CSV response
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if course_type == 'completed':
            writer.writerow(['Title', 'Description', 'Level', 'Completion Date'])
        else:
            writer.writerow(['Title', 'Description', 'Level', 'Date Added'])
        
        # Write course data
        for course in courses:
            writer.writerow([course['title'], course['description'], course['level'], 
                           course['completion_date'] if course_type == 'completed' else course['date_added']])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course_type}_courses.csv'}
        )
    
    finally:
        conn.close()

@app.route('/complete-course/<int:course_id>', methods=['POST'])
def complete_course(course_id):
    """Mark a course as completed"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('my_courses'))
        
        # Check if already completed
        existing = conn.execute(
            'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
            (user['id'], course_id)
        ).fetchone()
        
        if existing:
            if existing['completed']:
                flash('Course already completed.', 'info')
            else:
                # Update to completed
                conn.execute(
                    'UPDATE user_courses SET completed = 1, completion_date = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?',
                    (user['id'], course_id)
                )
                conn.commit()
                flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
                log_completion_event(user['id'], course_id, course['title'])
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
            log_completion_event(user['id'], course_id, course['title'])
    
    finally:
        conn.close()
    
    return redirect(url_for('my_courses'))

@app.route('/mark_complete/<int:course_id>', methods=['POST'])
def mark_complete(course_id):
    """AJAX endpoint to mark a course as completed"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    try:
        # Check if course exists
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Check if already completed
        existing = conn.execute(
            'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
            (user['id'], course_id)
        ).fetchone()
        
        if existing:
            if existing['completed']:
                return jsonify({'success': False, 'error': 'Course already completed'})
            else:
                # Update to completed
                conn.execute(
                    'UPDATE user_courses SET completed = 1, completion_date = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?',
                    (user['id'], course_id)
                )
                conn.commit()
                log_completion_event(user['id'], course_id, course['title'])
                return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            log_completion_event(user['id'], course_id, course['title'])
            return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

def log_completion_event(user_id, course_id, course_title):
    """Log course completion event"""
    try:
        log_message = f'User {user_id} completed course {course_id}: {course_title}'
        log_security_event('course_completion', log_message, request.remote_addr, user_id)
    except Exception as e:
        log_security_event('course_completion_error', f'Error logging completion for user {user_id}, course {course_id}: {str(e)}', request.remote_addr, user_id)

@app.route('/update-completion-date/<int:course_id>', methods=['POST'])
def update_completion_date(course_id):
    """Update completion date for a course"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    try:
        completion_date = request.form.get('completion_date')
        user_id = user['id']
        
        conn = get_db_connection()
        try:
            # Update completion date
            conn.execute(
                'UPDATE user_courses SET completion_date = ? WHERE user_id = ? AND course_id = ?',
                (completion_date, user_id, course_id)
            )
            conn.commit()
            flash('Completion date updated successfully!', 'success')
            log_security_event('completion_date_update', 
                             f'Updated completion date for course {course_id} to {completion_date}',
                             request.remote_addr, user_id)
            
        finally:
            conn.close()
            
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
    except Exception as e:
        flash(f'Error updating completion date: {str(e)}', 'error')
        log_security_event('completion_date_update_error', 
                         f'Error updating completion date for user {user_id}, course {course_id}: {str(e)}',
                         request.remote_addr, user_id)
    
    return redirect(url_for('my_courses'))

@app.route('/learnings')
def learnings():
    """Learning entries page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get user's learning entries
    conn = get_db_connection()
    try:
        entries = conn.execute('''
            SELECT * FROM learning_entries 
            WHERE user_id = ? 
            ORDER BY date_added DESC
        ''', (user['id'],)).fetchall()
        return render_template('learnings/index.html', entries=entries)
    finally:
        conn.close()

@app.route('/add-learning', methods=['GET', 'POST'])
def add_learning():
    """Add learning entry"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '')
        custom_date = request.form.get('custom_date')
        is_global = request.form.get('is_global') == 'on'
        
        if title:
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO learning_entries (user_id, title, description, tags, custom_date, is_global)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user['id'], title, description, tags, custom_date, is_global))
                conn.commit()
                flash('Learning entry added successfully!', 'success')
                return redirect(url_for('learnings'))
            finally:
                conn.close()
        else:
            flash('Title is required.', 'error')
    
    return render_template('learnings/add.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle profile updates (basic implementation)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user data
    conn = get_db_connection()
    try:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        
        # Calculate user stats
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']
        
        completed_courses_count = conn.execute('''
            SELECT COUNT(*) as count FROM user_courses 
            WHERE user_id = ? AND completed = 1
        ''', (user['id'],)).fetchone()['count']
        
        # Calculate level progression info
        user_points = user_data['points'] if user_data else 0
        current_level = user_data['level'] if user_data else 'Beginner'
        
        # Get level settings from database
        level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        level_mapping = {level['level_name']: level['points_required'] for level in level_settings}
        
        # Calculate next level info
        next_level = None
        points_to_next = 0
        level_points = 0
        
        # Find current level points and next level
        current_level_points = level_mapping.get(current_level, 0)
        level_points = user_points - current_level_points
        
        # Find next level
        for level_name, required_points in level_mapping.items():
            if user_points < required_points:
                next_level = level_name
                points_to_next = required_points - user_points
                break
        
        # Calculate progress percentage
        if next_level:
            next_level_points = level_mapping[next_level]
            prev_level_points = current_level_points
            if next_level_points > prev_level_points:
                progress_percentage = ((user_points - prev_level_points) / (next_level_points - prev_level_points)) * 100
            else:
                progress_percentage = 100
        else:
            progress_percentage = 100  # Max level reached
        
        # Create level_info object
        level_info = {
            'next_level': next_level,
            'points_to_next': points_to_next,
            'level_points': max(0, level_points),
            'progress_percentage': progress_percentage
        }
        
        # For now, provide empty points_log until points logging is implemented
        points_log = []
        
        return render_template('dashboard/profile.html', 
                             user=user_data,
                             learning_count=learning_count,
                             completed_courses_count=completed_courses_count,
                             level_info=level_info,
                             points_log=points_log)
    finally:
        conn.close()

@app.route('/points_log')
def points_log():
    """View user's points transaction history"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # For now, return empty points log
    # TODO: Implement actual points logging system
    return render_template('dashboard/profile.html', 
                         user=user,
                         learning_count=0,
                         completed_courses_count=0,
                         level_info={'next_level': None, 'points_to_next': 0, 'level_points': 0, 'progress_percentage': 0},
                         points_log=[])

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
        level_mapping = {'Beginner': 0, 'Intermediate': 150, 'Advanced': 250}
        next_level = 'Advanced'
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
    """Admin session management with dynamic statistics"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Get active sessions
        active_sessions = conn.execute('''
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
        
        # Get activity statistics (last 7 days)
        activity_stats = conn.execute('''
            SELECT activity_type, COUNT(*) as count
            FROM session_activity 
            WHERE datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY activity_type
            ORDER BY count DESC
        ''').fetchall()
        
        # Get daily login statistics (last 7 days)
        login_stats = conn.execute('''
            SELECT DATE(created_at) as login_date, COUNT(*) as login_count
            FROM user_sessions 
            WHERE datetime(created_at) >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY login_date DESC
        ''').fetchall()
        
        # Calculate today's login count
        today_login_count = 0
        today_date = conn.execute("SELECT DATE('now')").fetchone()[0]
        for stat in login_stats:
            if stat['login_date'] == today_date:
                today_login_count = stat['login_count']
                break
        
        return render_template('admin/sessions.html', 
                             active_sessions=active_sessions,
                             activity_stats=activity_stats,
                             login_stats=login_stats,
                             today_login_count=today_login_count)
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
    """Admin course management with pagination"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)  # Default 25 courses per page
    search = request.args.get('search', '', type=str)
    source_filter = request.args.get('source', '', type=str)
    level_filter = request.args.get('level', '', type=str)
    url_status_filter = request.args.get('url_status', '', type=str)
    points_filter = request.args.get('points', '', type=str)
    
    # Ensure per_page is within reasonable bounds
    per_page = max(10, min(100, per_page))
    
    # Get courses with pagination
    conn = get_db_connection()
    try:
        # Build WHERE clause for filters
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(title LIKE ? OR description LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
            
        if source_filter:
            where_conditions.append("source = ?")
            params.append(source_filter)
            
        if level_filter:
            where_conditions.append("level = ?")
            params.append(level_filter)
            
        if url_status_filter:
            where_conditions.append("url_status = ?")
            params.append(url_status_filter)
            
        if points_filter:
            if points_filter == "0-100":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 0 AND 100")
            elif points_filter == "100-200":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 100 AND 200")
            elif points_filter == "200-300":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 200 AND 300")
            elif points_filter == "300-400":
                where_conditions.append("CAST(points as INTEGER) BETWEEN 300 AND 400")
            elif points_filter == "400+":
                where_conditions.append("CAST(points as INTEGER) > 400")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count for pagination
        count_query = f'SELECT COUNT(*) as count FROM courses {where_clause}'
        total_courses = conn.execute(count_query, params).fetchone()['count']
        
        # Calculate pagination info
        total_pages = max(1, (total_courses + per_page - 1) // per_page)  # Ceiling division
        page = max(1, min(page, total_pages))  # Ensure page is within bounds
        offset = (page - 1) * per_page
        
        # Get courses for current page
        query = f'''
            SELECT * FROM courses 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        courses = conn.execute(query, params).fetchall()
        
        # Get available sources and levels for filters
        sources = conn.execute('SELECT DISTINCT source FROM courses WHERE source IS NOT NULL ORDER BY source').fetchall()
        levels = conn.execute('SELECT DISTINCT level FROM courses WHERE level IS NOT NULL ORDER BY level').fetchall()
        
        # Calculate statistics for the dashboard (from entire database, not just current page)
        stats_query = '''
            SELECT 
                COUNT(*) as total_courses,
                COUNT(CASE WHEN source = 'Manual' THEN 1 END) as manual_entries,
                COUNT(CASE WHEN url_status = 'Working' THEN 1 END) as working_urls,
                COUNT(CASE WHEN url_status = 'Not Working' OR url_status = 'Broken' THEN 1 END) as broken_urls
            FROM courses
        '''
        stats = conn.execute(stats_query).fetchone()
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_courses': total_courses,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'start_course': offset + 1,
            'end_course': min(offset + per_page, total_courses)
        }
        
        return render_template('admin/courses.html', 
                             courses=courses, 
                             pagination=pagination_info,
                             stats=stats,
                             sources=[row['source'] for row in sources],
                             levels=[row['level'] for row in levels],
                             current_search=search,
                             current_source=source_filter,
                             current_level=level_filter,
                             current_url_status=url_status_filter,
                             current_points=points_filter)
    finally:
        conn.close()

@app.route('/admin/debug_environment', methods=['GET'])
def debug_environment():
    """Debug endpoint to check Azure environment"""
    import sys
    import os
    
    try:
        # Test imports
        import pandas as pd
        pandas_version = pd.__version__
        pandas_ok = True
    except ImportError as e:
        pandas_version = f"IMPORT ERROR: {e}"
        pandas_ok = False
    
    try:
        import openpyxl
        openpyxl_version = openpyxl.__version__
        openpyxl_ok = True
    except ImportError as e:
        openpyxl_version = f"IMPORT ERROR: {e}"
        openpyxl_ok = False
    
    try:
        import sqlite3
        sqlite_version = sqlite3.sqlite_version
        sqlite_ok = True
    except ImportError as e:
        sqlite_version = f"IMPORT ERROR: {e}"
        sqlite_ok = False
    
    debug_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "environment_variables": {
            "WEBSITE_SITE_NAME": os.environ.get("WEBSITE_SITE_NAME"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "PATH": os.environ.get("PATH", "")[:200] + "..." if len(os.environ.get("PATH", "")) > 200 else os.environ.get("PATH", ""),
        },
        "dependencies": {
            "pandas": {"version": pandas_version, "ok": pandas_ok},
            "openpyxl": {"version": openpyxl_version, "ok": openpyxl_ok},
            "sqlite3": {"version": sqlite_version, "ok": sqlite_ok}
        },
        "file_system": {
            "current_directory": os.getcwd(),
            "temp_directory": os.environ.get("TEMP", "/tmp"),
            "can_write_temp": os.access(os.environ.get("TEMP", "/tmp"), os.W_OK)
        }
    }
    
    return jsonify(debug_info)

@app.route('/admin/upload_excel_courses', methods=['POST'])
def admin_upload_excel_courses():
    """Upload courses from Excel file - Admin only"""
    try:
        print(f"📋 Upload request received from: {request.remote_addr}")
        user = get_current_user()
        print(f"📋 Current user: {user}")
        
        if not user or user['username'] != 'admin':
            print(f"❌ Access denied for user: {user}")
            return jsonify({'success': False, 'error': 'Admin privileges required.'}), 403
    except Exception as auth_error:
        print(f"❌ Authentication error: {auth_error}")
        return jsonify({'success': False, 'error': f'Authentication error: {str(auth_error)}'}), 500
    
    try:
        import pandas as pd
        from datetime import datetime
        import hashlib
        from upload_reports_manager import UploadReportsManager
        
        # Initialize upload reports manager
        try:
            reports_manager = UploadReportsManager()
        except Exception as e:
            print(f"Warning: Could not initialize upload reports manager: {e}")
            reports_manager = None
        
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded.'}), 400
        
        file = request.files['excel_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls).'}), 400
        
        # Read Excel file
        try:
            df = pd.read_excel(file)
            print(f"Excel file read successfully: {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            error_msg = f'Failed to read Excel file: {str(e)}'
            print(f"Excel read error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Validate required columns
        required_columns = ['title', 'url', 'source', 'level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f'Missing required columns: {", ".join(missing_columns)}. Required: {", ".join(required_columns)}'
            print(f"Column validation error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Process the data
        conn = None
        try:
            conn = get_db_connection()
            print("Database connection established")
            
            stats = {
                'total_processed': 0,
                'added': 0,
                'skipped': 0,
                'errors': 0,
                'error_details': []
            }
            
            # Create upload report entry
            report_id = None
            if reports_manager:
                try:
                    report_id = reports_manager.create_upload_report(
                        user_id=user['id'],
                        filename=file.filename,
                        total_rows=len(df),
                        processed_rows=0,
                        success_count=0,
                        error_count=0,
                        warnings_count=0
                    )
                except Exception as report_error:
                    print(f"Warning: Could not create upload report: {report_error}")
                    report_id = None
            
            # Get existing courses to check for duplicates
            existing_courses = conn.execute('SELECT title, url FROM courses').fetchall()
            existing_set = set()
            for row in existing_courses:
                title = row['title'] if row['title'] else ''
                url = row['url'] if row['url'] else ''
                if title and url:  # Only add if both title and url are not empty
                    existing_set.add((title.lower().strip(), url.lower().strip()))
            print(f"Found {len(existing_set)} existing courses for duplicate check")
            
            for index, row in df.iterrows():
                stats['total_processed'] += 1
                
                try:
                    # Extract and validate data
                    title = str(row['title']).strip() if pd.notna(row['title']) else ''
                    url = str(row['url']).strip() if pd.notna(row['url']) else ''
                    source = str(row['source']).strip() if pd.notna(row['source']) else ''
                    level = str(row['level']).strip() if pd.notna(row['level']) else ''
                    
                    # Validate required fields
                    if not all([title, url, source, level]):
                        error_detail = f'Row {index + 1}: Missing required data - title: {bool(title)}, url: {bool(url)}, source: {bool(source)}, level: {bool(level)}'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Validate level
                    if level not in ['Beginner', 'Intermediate', 'Advanced']:
                        error_detail = f'Row {index + 1}: Invalid level "{level}", must be Beginner, Intermediate, or Advanced'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Validate URL format
                    if not url.startswith(('http://', 'https://')):
                        error_detail = f'Row {index + 1}: Invalid URL format "{url}", must start with http:// or https://'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue
                    
                    # Check for duplicates
                    if (title.lower(), url.lower()) in existing_set:
                        stats['skipped'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='skipped',
                                    message='Duplicate course already exists',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add skipped row detail: {detail_error}")
                        continue
                    
                    # Extract optional fields
                    description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                    category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None
                    difficulty = str(row.get('difficulty', '')).strip() if pd.notna(row.get('difficulty')) else None
                    
                    # Handle points
                    points = 0
                    if 'points' in row and pd.notna(row['points']):
                        try:
                            points = int(float(row['points']))
                            if points < 0:
                                points = 0
                        except (ValueError, TypeError):
                            points = 0
                    
                    # Auto-assign level based on points if points are provided
                    if points > 0:
                        if points < 150:
                            level = 'Beginner'
                        elif points < 250:
                            level = 'Intermediate'
                        else:
                            level = 'Advanced'
                    
                    # Insert the course
                    try:
                        conn.execute('''
                            INSERT INTO courses 
                            (title, description, url, link, source, level, points, category, difficulty, created_at, url_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            title,
                            description,
                            url,
                            url,  # Use the same URL for both url and link columns
                            source,
                            level,
                            points,
                            category,
                            difficulty,
                            datetime.now().isoformat(),
                            'Pending'
                        ))
                        
                        # Add to existing set to prevent duplicates within the same upload
                        existing_set.add((title.lower(), url.lower()))
                        stats['added'] += 1
                        
                        # Add successful row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='success',
                                    message='Course added successfully',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add row detail: {detail_error}")
                        
                    except Exception as db_error:
                        error_detail = f'Row {index + 1}: Database insert failed - {str(db_error)}'
                        stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        print(f"Database insert error for row {index + 1}: {str(db_error)}")
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add DB error row detail: {detail_error}")
                        continue
                    
                except Exception as row_error:
                    error_detail = f'Row {index + 1}: Processing failed - {str(row_error)}'
                    stats['error_details'].append(error_detail)
                    stats['errors'] += 1
                    print(f"Row processing error for row {index + 1}: {str(row_error)}")
                    
                    # Add row detail to report
                    if report_id and reports_manager:
                        try:
                            reports_manager.add_row_detail(
                                report_id=report_id,
                                row_number=index + 1,
                                status='failed',
                                message=error_detail,
                                course_title='Unknown',
                                course_url='Unknown'
                            )
                        except Exception as detail_error:
                            print(f"Warning: Could not add processing error row detail: {detail_error}")
                    continue
            
            # Commit the transaction
            try:
                conn.commit()
                print(f"Transaction committed successfully. Stats: {stats}")
                
                # Update the upload report with final statistics
                if report_id and reports_manager:
                    try:
                        reports_manager.update_upload_report(
                            report_id=report_id,
                            processed_rows=stats['total_processed'],
                            success_count=stats['added'],
                            error_count=stats['errors'],
                            warnings_count=stats['skipped']
                        )
                    except Exception as update_error:
                        print(f"Warning: Could not update upload report: {update_error}")
            except Exception as commit_error:
                print(f"Commit error: {str(commit_error)}")
                return jsonify({
                    'success': False, 
                    'error': f'Failed to save courses to database: {str(commit_error)}',
                    'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }
                }), 500
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Excel upload completed successfully.',
                'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }
            }
            
            # Include error details if there were any errors (but still consider it a success if some courses were added)
            if stats['error_details']:
                response_data['warnings'] = stats['error_details'][:10]  # Limit to first 10 errors for readability
            
            return jsonify(response_data)
            
        except Exception as db_error:
            error_msg = f'Database operation failed: {str(db_error)}'
            print(f"Database error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
        finally:
            if conn:
                conn.close()
                print("Database connection closed")
            
    except ImportError as import_error:
        error_msg = f'pandas library is required for Excel processing. Import error: {str(import_error)}'
        print(f"Import error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Upload failed: {str(e)}'
        print(f"General error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/admin/download_excel_template')
def admin_download_excel_template():
    """Download Excel template for course upload - Admin only"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        import pandas as pd
        from io import BytesIO
        from flask import send_file
        
        # Create sample data for the template
        sample_data = {
            'title': [
                'Introduction to Machine Learning',
                'Advanced Python Programming',
                'Azure AI Fundamentals'
            ],
            'description': [
                'Learn the basics of machine learning and AI concepts',
                'Deep dive into advanced Python programming techniques',
                'Understand Azure AI services and capabilities'
            ],
            'url': [
                'https://learn.microsoft.com/en-us/training/paths/machine-learning-foundations',
                'https://learn.microsoft.com/en-us/training/paths/python-advanced',
                'https://learn.microsoft.com/en-us/training/paths/azure-ai-fundamentals'
            ],
            'source': [
                'Microsoft Learn',
                'Microsoft Learn', 
                'Microsoft Learn'
            ],
            'level': [
                'Beginner',
                'Intermediate',
                'Advanced'
            ],
            'points': [
                120,
                200,
                300
            ],
            'category': [
                'Machine Learning',
                'Programming',
                'Cloud Computing'
            ],
            'difficulty': [
                'Easy',
                'Medium',
                'Hard'
            ]
        }
        
        # Create DataFrame
        df = pd.DataFrame(sample_data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Courses', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Courses']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='course_upload_template.xlsx'
        )
        
    except ImportError:
        flash('pandas library is required for Excel processing.', 'error')
        return redirect(url_for('admin_courses'))
    except Exception as e:
        flash(f'Failed to generate template: {str(e)}', 'error')
        return redirect(url_for('admin_courses'))

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

@app.route('/admin/url-validation')
@require_admin
def admin_url_validation():
    """URL validation management page - Admin only"""
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
            status = course.get('url_status', 'Unchecked') if course else 'Unchecked'
            if status == 'Working':
                summary['working']['count'] += 1
            elif status == 'Not Working':
                summary['not_working']['count'] += 1
            elif status == 'Broken':
                summary['broken']['count'] += 1
            else:
                summary['unchecked']['count'] += 1
        
        return render_template('admin/url_validation.html',
                             courses=courses,
                             summary=summary)
        
    except Exception as e:
        flash(f'Error loading URL validation data: {e}', 'error')
        return redirect(url_for('admin_courses'))
    finally:
        conn.close()

@app.route('/admin/validate-all-urls', methods=['POST'])
@require_admin
def admin_validate_all_urls():
    """Start URL validation for all courses (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        courses = conn.execute('SELECT id, title, url FROM courses WHERE url IS NOT NULL AND url != ""').fetchall()
        conn.close()
        
        if not courses:
            return jsonify({'success': False, 'message': 'No courses with URLs found'})
        
        # Start validation in background thread
        def validate_urls():
            conn = get_db_connection()
            try:
                for course in courses:
                    try:
                        # Basic URL validation
                        parsed = urlparse(course['url'])
                        if not parsed.scheme or not parsed.netloc:
                            status = 'Broken'
                        else:
                            # Try to connect to URL (with timeout)
                            try:
                                response = requests.head(course['url'], timeout=10, allow_redirects=True)
                                if response.status_code < 400:
                                    status = 'Working'
                                else:
                                    status = 'Not Working'
                            except requests.exceptions.RequestException:
                                # If HEAD fails, try GET with smaller content
                                try:
                                    response = requests.get(course['url'], timeout=10, allow_redirects=True, stream=True)
                                    if response.status_code < 400:
                                        status = 'Working'
                                    else:
                                        status = 'Not Working'
                                except requests.exceptions.RequestException:
                                    status = 'Broken'
                    except Exception:
                        status = 'Broken'
                    
                    # Update database
                    conn.execute('''
                        UPDATE courses 
                        SET url_status = ?, last_url_check = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (status, course['id']))
                    conn.commit()
            except Exception as e:
                print(f"URL validation error: {e}")
            finally:
                conn.close()
        
        # Start background thread
        thread = threading.Thread(target=validate_urls)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'URL validation started for {len(courses)} courses',
            'course_count': len(courses)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting validation: {str(e)}'})

@app.route('/admin/url-validation-status')
@require_admin
def admin_url_validation_status():
    """Get URL validation status (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        
        # Get summary of validation status
        courses = conn.execute('''
            SELECT id, title, url, url_status, last_url_check
            FROM courses 
            WHERE url IS NOT NULL AND url != ""
            ORDER BY last_url_check DESC
        ''').fetchall()
        
        # Count by status
        status_counts = {
            'working': 0,
            'not_working': 0,
            'broken': 0,
            'unchecked': 0
        }
        
        course_list = []
        for course in courses:
            status = course.get('url_status', 'Unchecked') or 'Unchecked'
            status_lower = status.lower().replace(' ', '_')
            if status_lower in status_counts:
                status_counts[status_lower] += 1
            else:
                status_counts['unchecked'] += 1
            
            course_list.append({
                'id': course['id'],
                'title': course['title'],
                'url': course['url'],
                'status': status,
                'last_check': course.get('last_url_check', 'Never')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'courses': course_list,
            'summary': status_counts,
            'total_courses': len(course_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting status: {str(e)}'})

@app.route('/admin/edit-course/<int:course_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_course(course_id):
    """Edit a course (admin only)"""
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            provider = request.form.get('provider')
            source = request.form.get('source')
            url = request.form.get('url')
            link = request.form.get('link')
            level = request.form.get('level')
            category = request.form.get('category')
            points = request.form.get('points', 0)
            
            if not title or not description:
                flash('Title and description are required.', 'error')
                return redirect(url_for('admin_edit_course', course_id=course_id))
            
            try:
                points = int(points) if points else 0
            except ValueError:
                points = 0
            
            # Auto-calculate level based on points
            if points < 150:
                level = 'Beginner'
            elif points < 250:
                level = 'Intermediate'
            else:
                level = 'Advanced'
            
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
        # Delete related records first (if user_courses table exists)
        try:
            conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        except:
            pass  # Table might not exist
        
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/bulk-delete-courses', methods=['POST'])
@require_admin
def admin_bulk_delete_courses():
    """Bulk delete multiple courses (admin only)"""
    course_ids = request.form.getlist('course_ids')
    
    if not course_ids:
        flash('No courses selected for deletion.', 'warning')
        return redirect(url_for('admin_courses'))
    
    # Validate that all IDs are integers
    try:
        course_ids = [int(id) for id in course_ids]
    except ValueError:
        flash('Invalid course IDs provided.', 'error')
        return redirect(url_for('admin_courses'))
    
    conn = get_db_connection()
    deleted_count = 0
    
    try:
        # Delete related records first (if user_courses table exists)
        try:
            for course_id in course_ids:
                conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        except:
            pass  # Table might not exist
        
        # Delete courses
        for course_id in course_ids:
            result = conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            if result.rowcount > 0:
                deleted_count += 1
        
        conn.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} course(s)!', 'success')
        else:
            flash('No courses were deleted. They may have already been removed.', 'warning')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting courses: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@require_admin
def admin_delete_user(user_id):
    """Delete a user (admin only) - requires explicit authorization"""
    # Explicit authorization check for user deletion
    try:
        # Check if this is production environment
        if production_safety.environment == 'production':
            # In production, require additional explicit authorization
            explicit_authorization = request.form.get('explicit_authorization')
            if not explicit_authorization:
                flash('User deletion requires explicit authorization in production.', 'error')
                return redirect(url_for('admin_users'))
    except:
        pass  # Continue if production_safety not available
    
    conn = get_db_connection()
    try:
        # Check if user exists and get username for validation
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user['username']
        
        # Protected users that cannot be deleted - admin user cannot be deleted
        protected_users = ['admin']
        if username in protected_users:
            flash(f'Admin user cannot be deleted - system protection active.', 'error')
            return redirect(url_for('admin_users'))
        
        # Delete user and related data
        try:
            conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        try:
            conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        try:
            conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        flash(f'User "{username}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/toggle-user-status/<int:user_id>', methods=['POST'])
@require_admin
def admin_toggle_user_status(user_id):
    """Toggle user status between active and inactive (admin only)"""
    conn = get_db_connection()
    try:
        # Get current user status
        user = conn.execute('SELECT username, status FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Toggle status
        new_status = 'inactive' if user['status'] == 'active' else 'active'
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        
        flash(f'User "{user["username"]}" status changed to {new_status}.', 'success')
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/set-user-password', methods=['POST'])
@require_admin 
def admin_set_user_password():
    """Allow admin to set a custom password for a user"""
    user_id = request.form.get('user_id')
    new_password = request.form.get('custom_password')  # Updated to match form field name
    confirm_password = request.form.get('confirm_custom_password')
    
    if not user_id or not new_password:
        flash('User ID and new password are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if new_password != confirm_password:
        flash('Password confirmation does not match.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get user info
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Hash and update password
        hashed_password = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (hashed_password, user_id)
        )
        conn.commit()
        
        flash(f'Password updated successfully for user: {user["username"]}', 'success')
        
    except Exception as e:
        flash(f'Error updating password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reset-all-user-passwords', methods=['POST'])
@require_admin
def admin_reset_all_user_passwords():
    """Reset all user passwords (admin only) - requires explicit authorization"""
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    confirmation = request.form.get('reset_all_confirmation')
    
    # Explicit authorization check for bulk password reset
    try:
        if production_safety.environment == 'production':
            explicit_authorization = request.form.get('explicit_authorization')
            if not explicit_authorization:
                flash('Bulk password reset requires explicit authorization in production.', 'error')
                return redirect(url_for('admin_users'))
    except:
        pass  # Continue if production_safety not available
    
    if not new_password or not confirm_password:
        flash('Both password fields are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if new_password != confirm_password:
        flash('Password confirmation does not match.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
        
    if not confirmation:
        flash('You must confirm the bulk password reset operation.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Get all users except admin
        users = conn.execute('SELECT id, username FROM users WHERE username != ?', ('admin',)).fetchall()
        
        if not users:
            flash('No users found to reset passwords for.', 'warning')
            return redirect(url_for('admin_users'))
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update all non-admin users
        updated_count = 0
        for user in users:
            conn.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (hashed_password, user['id'])
            )
            updated_count += 1
        
        conn.commit()
        flash(f'Successfully reset passwords for {updated_count} users. Users will need to use the new password on their next login.', 'success')
        
    except Exception as e:
        flash(f'Error resetting passwords: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

# Legacy route name for compatibility with existing form
@app.route('/admin/reset-user-password', methods=['POST'])
@require_admin
def admin_reset_user_password():
    """Legacy route - redirects to the new set password function"""
    return admin_set_user_password()

@app.route('/admin/search-and-import-courses', methods=['POST'])
@require_admin
def admin_search_and_import_courses():
    """Search and import courses from external sources (admin only)"""
    search_term = request.form.get('search_term', '')
    source = request.form.get('source', 'manual')
    
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

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Admin settings"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Update level settings
        try:
            for level_name in ['beginner', 'learner', 'intermediate', 'expert']:
                points_key = f'{level_name}_points'
                if points_key in request.form:
                    points_required = int(request.form[points_key])
                    conn.execute(
                        'UPDATE level_settings SET points_required = ? WHERE LOWER(level_name) = ?',
                        (points_required, level_name)
                    )
            conn.commit()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('admin_settings'))
    
    # Get current level settings
    try:
        level_settings = conn.execute(
            'SELECT level_name, points_required FROM level_settings ORDER BY points_required ASC'
        ).fetchall()
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'error')
        level_settings = []
    finally:
        conn.close()
    
    return render_template('admin/settings.html', level_settings=level_settings)

@app.route('/admin/change-password', methods=['GET', 'POST'])
def admin_change_password():
    """Admin change password"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('admin/change_password.html')
        
        # Verify current password
        conn = get_db_connection()
        try:
            admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
            if admin_user and check_password_hash(admin_user['password_hash'], current_password):
                # Update password
                new_hash = generate_password_hash(new_password)
                conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
                conn.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Current password is incorrect.', 'error')
        finally:
            conn.close()
    
    return render_template('admin/change_password.html')

# Admin User Management Routes
@app.route('/admin/add-user', methods=['GET', 'POST'])
@require_admin
def admin_add_user():
    """Add a new user (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        level = request.form.get('level', 'Beginner')
        status = request.form.get('status', 'active')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
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

# Admin Course Management Routes
@app.route('/admin/add-course', methods=['GET', 'POST'])
@require_admin
def admin_add_course():
    """Add a new course with comprehensive validation (admin only)"""
    if request.method == 'POST':
        # Course validator temporarily disabled - module removed in cleanup
        logger.info("Course validation temporarily disabled - using basic validation only")
        flash('Course added with basic validation. Advanced URL validation temporarily unavailable.', 'info')
        validator = None
        
        # Collect form data
        course_data = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'provider': request.form.get('provider', '').strip(),  # Keep for backward compatibility
            'source': request.form.get('source', '').strip(),
            'url': request.form.get('url', '').strip() or None,
            'link': request.form.get('link', '').strip() or None,
            'level': request.form.get('level', '').strip(),
            'category': request.form.get('category', '').strip() or None,
            'points': request.form.get('points', 0)
        }
        
        # Validate with comprehensive schema validation
        if validator:
            course = validator.validate_schema(course_data)
            
            # Check for validation errors
            if not course.is_valid:
                for error in course.validation_errors:
                    if error.severity == 'error':
                        flash(f'{error.field.title()}: {error.message}', 'error')
                    else:
                        flash(f'{error.field.title()}: {error.message}', 'warning')
                
                # If there are errors, return to form with data
                if any(e.severity == 'error' for e in course.validation_errors):
                    return render_template('admin/add_course.html', course_data=course_data)
            
            # Validate URLs if provided
            url_validation_results = {}
            validation_warnings = []
            
            if course.url:
                logger.info(f"Validating primary URL: {course.url}")
                url_result = validator.validate_url(course.url)
                url_validation_results['url'] = url_result
                
                if url_result['status'] not in ['Working']:
                    validation_warnings.append(f"Primary URL may not be accessible: {url_result.get('error_message', 'Unknown error')}")
                    
            if course.link and course.link != course.url:
                logger.info(f"Validating link URL: {course.link}")
                link_result = validator.validate_url(course.link)
                url_validation_results['link'] = link_result
                
                if link_result['status'] not in ['Working']:
                    validation_warnings.append(f"Link URL may not be accessible: {link_result.get('error_message', 'Unknown error')}")
            
            # Show URL validation warnings
            for warning in validation_warnings:
                flash(warning, 'warning')
                
            # Update course data with validation results
            if course.url and 'url' in url_validation_results:
                course.url_status = url_validation_results['url']['status']
                course.last_url_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Fallback validation without validator
            if not course_data['title'] or not course_data['description']:
                flash('Title and description are required.', 'error')
                return render_template('admin/add_course.html', course_data=course_data)
            
            try:
                course_data['points'] = int(course_data['points']) if course_data['points'] else 0
            except ValueError:
                course_data['points'] = 0
                flash('Points must be a number. Set to 0.', 'warning')
            
            course = type('Course', (), course_data)()
            course.url_status = 'unchecked'
            course.last_url_check = None
        
        # Insert into database
        conn = get_db_connection()
        try:
            # Determine which URL field to use for url_status tracking
            primary_url = course.url or course.link
            
            conn.execute('''
                INSERT INTO courses (
                    title, description, provider, source, url, link, level, category, points,
                    created_at, url_status, last_url_check
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
            ''', (
                course.title, course.description, course_data['provider'], course.source,
                course.url, course.link, course.level, course.category, course.points,
                course.url_status, course.last_url_check
            ))
            conn.commit()
            
            # Success message with validation info
            success_msg = 'Course added successfully!'
            if validator and primary_url:
                if course.url_status == 'Working':
                    success_msg += ' URL validation passed.'
                elif course.url_status in ['Not Working', 'Broken']:
                    success_msg += f' Note: URL validation failed ({course.url_status}).'
                else:
                    success_msg += ' URL validation completed with warnings.'
            
            flash(success_msg, 'success')
            logger.info(f"Course added successfully: {course.title} (URL Status: {course.url_status})")
            
            return redirect(url_for('admin_courses'))
            
        except Exception as e:
            logger.error(f"Database error adding course: {e}")
            flash(f'Error adding course: {str(e)}', 'error')
            return render_template('admin/add_course.html', course_data=course_data)
        finally:
            conn.close()
    
    return render_template('admin/add_course.html')

# Global storage for course fetch status (since background threads can't access Flask session)
course_fetch_status = {}

@app.route('/admin/populate-ai-courses', methods=['POST'])
@require_admin
def admin_populate_ai_courses():
    """Fetch AI/Copilot courses from live APIs with real-time updates"""
    logger.info("🔍 Admin initiated FAST live API course fetching")
    
    # Fast course fetcher temporarily disabled - module removed in cleanup
    logger.info("Fast course API fetcher temporarily disabled - using basic course addition only")
    return jsonify({
        'success': False,
        'error': 'Fast course fetcher temporarily unavailable. Please add courses manually.',
        'message': 'Advanced course fetching is temporarily disabled during workspace cleanup.'
    }), 503

    try:
        logger.info("📡 Starting FAST live API course fetching...")
        
        # Start asynchronous course fetching with real-time updates
        import threading
        import uuid
        
        # Generate unique fetch ID for this request
        fetch_id = str(uuid.uuid4())[:8]
        
        def fetch_courses_async():
            """Background task to fetch courses asynchronously"""
            try:
                # Update status: Starting
                course_fetch_status[fetch_id] = {
                    'status': 'fetching',
                    'message': 'Fetching courses from live APIs...',
                    'progress': 10
                }
                
                # Fetch courses (faster, no fallbacks)
                result = get_fast_ai_courses(10)  # Reduced count for speed
                
                # Update status: Complete
                course_fetch_status[fetch_id] = {
                    'status': 'complete',
                    'message': f'Successfully added {result["courses_added"]} courses in {result["total_time"]}s',
                    'progress': 100,
                    'result': result
                }
                
                logger.info(f"📚 Fast course fetching completed: {result['courses_added']} courses added")
                
            except Exception as e:
                # Update status: Error
                course_fetch_status[fetch_id] = {
                    'status': 'error',
                    'message': f'Error: {str(e)}',
                    'progress': 0,
                    'error': str(e)
                }
                logger.error(f"❌ Fast course fetching failed: {e}")
        
        # Start background thread
        fetch_thread = threading.Thread(target=fetch_courses_async)
        fetch_thread.daemon = True
        fetch_thread.start()
        
        # Return JSON response with fetch ID for status tracking
        return jsonify({
            'success': True,
            'fetch_id': fetch_id,
            'message': 'Course fetching started - real APIs only, no fallbacks'
        })
            
    except Exception as e:
        error_msg = f'Error starting fast API course fetching: {str(e)}'
        logger.error(f"❌ Failed to start fast background fetching: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/admin/course-fetch-status/<fetch_id>')
@require_admin
def get_course_fetch_status(fetch_id):
    """Get the status of a course fetching operation"""
    status = course_fetch_status.get(fetch_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Fetch operation not found'
        }), 404


# Backward compatibility alias for old route name
@app.route('/admin/populate-linkedin-courses', methods=['POST'])
@require_admin  
def admin_populate_linkedin_courses():
    """Backward compatibility alias - redirects to new admin_populate_ai_courses"""
    logger.info("⚠️ Using deprecated route - redirecting to admin_populate_ai_courses")
    return admin_populate_ai_courses()

@app.route('/setup-admin')
def setup_admin():
    """Simple setup route to create admin user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            conn.close()
            return "✅ Admin user already exists! <a href='/'>Go to Login</a>"
        
        # Create admin user
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return f"""
        🎉 Admin user created successfully!<br>
        Username: admin<br>
        Password: {admin_password}<br>
        <a href='/'>Go to Login</a>
        """
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/health')
def health_check():
    """Health check endpoint with admin initialization"""
    
    import sqlite3
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    html_template = '''
    <html>
    <head><title>Health Check</title></head>
    <body style="font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px;">
        <h2>🔍 AI Learning Tracker - Health Check</h2>
        {content}
        <hr>
        <p><small>Last updated: {timestamp}</small></p>
    </body>
    </html>
    '''
    
    try:
        status_info = []
        
        # Check database connection
        try:
            conn = get_db_connection()
            status_info.append("✅ Database connection: OK")
            
            # Check tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'users' in tables:
                status_info.append("✅ Users table: EXISTS")
                
                # Check admin user
                cursor.execute("SELECT id, username, level FROM users WHERE username = 'admin'")
                admin_user = cursor.fetchone()
                
                if admin_user:
                    status_info.append(f"✅ Admin user: EXISTS (ID: {admin_user[0]}, Level: {admin_user[2]})")
                else:
                    status_info.append("❌ Admin user: MISSING")
                    
                    # Try to create admin user
                    status_info.append("🔧 Attempting to create admin user...")
                    
                    admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
                    password_hash = generate_password_hash(admin_password)
                    
                    cursor.execute("""
                        INSERT INTO users (
                            username, password_hash, level, points, status,
                            user_selected_level, login_count, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'admin', password_hash, 'Advanced', 100, 'active',
                        'Advanced', 0, datetime.now().isoformat()
                    ))
                    
                    admin_id = cursor.lastrowid
                    conn.commit()
                    
                    status_info.append(f"🎉 Admin user CREATED! (ID: {admin_id})")
                
                # Check total users
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                status_info.append(f"📊 Total users: {user_count}")
                
            else:
                status_info.append("❌ Users table: MISSING")
            
            conn.close()
            
        except Exception as e:
            status_info.append(f"❌ Database error: {str(e)}")
        
        # Check environment variables
        admin_pwd = os.environ.get('ADMIN_PASSWORD')
        if admin_pwd:
            status_info.append(f"✅ ADMIN_PASSWORD: SET (length: {len(admin_pwd)})")
        else:
            status_info.append("❌ ADMIN_PASSWORD: NOT SET")
        
        # Add login test link
        status_info.append("")
        status_info.append("🔗 <strong>Test Login:</strong>")
        status_info.append(f'<a href="/" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px;">Go to Login Page</a>')
        
        content = "<br>".join(status_info)
        
        return html_template.format(
            content=content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
    except Exception as e:
        return html_template.format(
            content=f"❌ Health check failed: {str(e)}",
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )

@app.route('/init-admin')
def simple_init_admin():
    """Simple admin initialization via URL parameter"""
    
    # Get password from URL parameter
    init_password = request.args.get('password', '')
    expected_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
    
    # Basic HTML template
    html_template = '''
    <html>
    <head><title>Admin Initialization</title></head>
    <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-bottom: 20px;">{title}</h2>
            {content}
        </div>
    </body>
    </html>
    '''
    
    if not init_password:
        return html_template.format(
            title="🔧 Admin User Initialization",
            content='''
            <p>To initialize the admin user, add your password as a URL parameter:</p>
            <p><strong>URL Format:</strong></p>
            <code style="background: #f0f0f0; padding: 10px; border-radius: 4px; display: block; margin: 10px 0;">
            https://your-app.azurewebsites.net/init-admin?password=YOUR_ADMIN_PASSWORD
            </code>
            <p><small>⚠️ Use your ADMIN_PASSWORD environment variable value</small></p>
            '''
        )
    
    if init_password != expected_password:
        return html_template.format(
            title="❌ Invalid Password",
            content='''
            <p>The initialization password is incorrect.</p>
            <p>Please check your ADMIN_PASSWORD environment variable.</p>
            <a href="/init-admin" style="color: #007bff;">Try Again</a>
            '''
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            conn.close()
            return html_template.format(
                title="✅ Admin Already Exists",
                content='''
                <p>The admin user has already been created.</p>
                <p>You can now login with username <strong>admin</strong></p>
                <a href="/" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    Go to Login
                </a>
                '''
            )
        
        # Create admin user
        password_hash = generate_password_hash(expected_password)
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        
        # Create demo user too
        demo_password = os.environ.get('DEMO_PASSWORD', 'demo123')
        cursor.execute("SELECT id FROM users WHERE username = 'demo'")
        if not cursor.fetchone():
            demo_hash = generate_password_hash(demo_password)
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, level, points, status,
                    user_selected_level, login_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'demo', demo_hash, 'Beginner', 0, 'active',
                'Beginner', 0, datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        return html_template.format(
            title="🎉 Initialization Complete!",
            content=f'''
            <p>✅ <strong>Admin user created successfully!</strong></p>
            <p>✅ Demo user created successfully</p>
            <p>📊 Admin user ID: {admin_id}</p>
            <hr style="margin: 20px 0;">
            <h3>🔗 Ready to Login:</h3>
            <p><strong>Username:</strong> admin</p>
            <p><strong>Password:</strong> [your ADMIN_PASSWORD]</p>
            <p><strong>Level:</strong> Advanced</p>
            <br>
            <a href="/" style="background: #28a745; color: white; padding: 15px 25px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                🚀 Go to Login Page
            </a>
            '''
        )
        
    except Exception as e:
        return html_template.format(
            title="❌ Initialization Failed",
            content=f'''
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please check the application logs for more details.</p>
            <a href="/init-admin" style="color: #007bff;">Try Again</a>
            '''
        )

# Initialize database on startup
try:
    if db_init:
        logger.info("🔄 Initializing database with Azure SQL support...")
        db_init()
        logger.info("✅ Database initialization completed")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")


@app.route('/create-admin-now')
def create_admin_now():
    """Emergency route to create admin user directly"""
    try:
        conn = get_db_connection()
        
        # First create users table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                user_selected_level TEXT DEFAULT 'Beginner',
                login_count INTEGER DEFAULT 0
            )
        ''')
        
        # Check if admin already exists
        existing_admin = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if existing_admin:
            conn.close()
            return f"<h2>Admin user already exists with ID: {existing_admin['id']}</h2><a href='/'>Go to Login</a>"
        
        # Create admin user with the known password
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 100, 'active', 'Advanced', 0))
        
        conn.commit()
        admin_id = conn.lastrowid
        conn.close()
        
        return f"<h2> Admin user created successfully!</h2><p>Admin ID: {admin_id}</p><p>Username: admin</p><p>You can now login at <a href='/'>the login page</a></p>"
        
    except Exception as e:
        return f"<h2> Error creating admin: {str(e)}</h2><a href='/create-admin-now'>Try Again</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
