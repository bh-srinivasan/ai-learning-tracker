"""
AI Learning Tracker - Clean Application Module
Refactored version with centralized database logic and clear separation between SQLite and Azure SQL
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
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pyodbc
except ImportError:
    pyodbc = None
    logger.warning("pyodbc not available - Azure SQL features will be disabled")

# Load environment variables from .env file
load_dotenv()

# Validate critical environment variables
def validate_environment_variables():
    """Validate that required environment variables are set"""
    env = os.environ.get('ENV', 'development')
    
    if env == 'production':
        required_vars = [
            'AZURE_SQL_SERVER',
            'AZURE_SQL_DATABASE', 
            'AZURE_SQL_USERNAME',
            'AZURE_SQL_PASSWORD',
            'ADMIN_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables for production: {missing_vars}")
            # Don't fail startup - just log the error
            logger.warning("App will run in limited mode without Azure SQL features")
        else:
            logger.info("All required environment variables are set for production")
    
    return True

# Validate environment on startup
validate_environment_variables()

app = Flask(__name__)

# Enhanced security configuration
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    'SESSION_COOKIE_SECURE': False,  # Set to False for local development (HTTP)
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=24)
})

# Database configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'ai_learning.db')

# Rate limiting
failed_attempts = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_ATTEMPTS = 5

# Session management
active_sessions = {}
session_lock = threading.Lock()

def is_azure_sql():
    """Check if all Azure SQL environment variables are set"""
    azure_server = os.environ.get('AZURE_SQL_SERVER')
    azure_database = os.environ.get('AZURE_SQL_DATABASE')
    azure_username = os.environ.get('AZURE_SQL_USERNAME')
    azure_password = os.environ.get('AZURE_SQL_PASSWORD')
    
    return all([azure_server, azure_database, azure_username, azure_password])

def is_azure_sql():
    """Check if all Azure SQL environment variables are set"""
    azure_server = os.environ.get('AZURE_SQL_SERVER')
    azure_database = os.environ.get('AZURE_SQL_DATABASE')
    azure_username = os.environ.get('AZURE_SQL_USERNAME')
    azure_password = os.environ.get('AZURE_SQL_PASSWORD')
    
    return all([azure_server, azure_database, azure_username, azure_password])

def get_session_table():
    """Get the appropriate session table name based on database backend"""
    return 'user_sessions' if is_azure_sql() else 'sessions'

def initialize_database():
    """Initialize database schema if missing"""
    logger.info("Initializing database schema...")
    
    conn = get_db_connection()
    try:
        if is_azure_sql():
            # Azure SQL Database schema initialization
            _initialize_azure_sql_schema(conn)
        else:
            # SQLite Database schema initialization
            _initialize_sqlite_schema(conn)
        
        logger.info("Database schema initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

def _initialize_azure_sql_schema(conn):
    """Initialize Azure SQL database schema"""
    logger.info("Initializing Azure SQL database schema")
    
    try:
        cursor = conn.cursor()
        
        # Check if user_sessions table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'user_sessions'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        # Create user_sessions table if it doesn't exist
        if not table_exists:
            logger.info("Creating user_sessions table in Azure SQL")
            cursor.execute("""
                CREATE TABLE user_sessions (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    session_token NVARCHAR(255) UNIQUE NOT NULL,
                    user_id INT NOT NULL,
                    ip_address NVARCHAR(45),
                    user_agent NVARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE(),
                    expires_at DATETIME NOT NULL,
                    is_active BIT DEFAULT 1,
                    last_activity DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
            logger.info("user_sessions table created successfully in Azure SQL")
        else:
            logger.info("user_sessions table already exists in Azure SQL")
        
    except Exception as e:
        logger.error(f"Error with Azure SQL schema initialization: {e}")
        raise

def _initialize_sqlite_schema(conn):
    """Initialize SQLite database schema"""
    logger.info("Initializing SQLite database schema")
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create sessions table (for SQLite compatibility)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create learning_entries table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT,
            hours_spent REAL,
            completed_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create courses table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT,
            duration_hours REAL,
            url TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create security_logs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            username TEXT,
            action TEXT,
            success INTEGER,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    logger.info("SQLite database schema initialized successfully")

def get_db_connection():
    """Get database connection based on environment configuration"""
    if is_azure_sql():
        # Azure SQL Database connection
        logger.info("Using Azure SQL Database with environment variables")
        return _get_azure_sql_connection()
    else:
        # Local SQLite Database connection
        logger.info(f"Using local SQLite database: {DATABASE_PATH}")
        return _get_sqlite_connection()

def _get_azure_sql_connection():
    """Get Azure SQL database connection"""
    try:
        import pyodbc
        
        azure_server = os.environ.get('AZURE_SQL_SERVER')
        azure_database = os.environ.get('AZURE_SQL_DATABASE')
        azure_username = os.environ.get('AZURE_SQL_USERNAME')
        azure_password = os.environ.get('AZURE_SQL_PASSWORD')
        
        # Build connection string from environment variables
        azure_connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server=tcp:{azure_server},1433;"
            f"Database={azure_database};"
            f"Uid={azure_username};"
            f"Pwd={azure_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        logger.info(f"Connecting to Azure SQL Database: {azure_database}")
        conn = pyodbc.connect(azure_connection_string)
        
        # Apply Azure SQL connection wrapper for SQLite compatibility
        return _wrap_azure_sql_connection(conn)
        
    except Exception as e:
        logger.error(f"Azure SQL connection failed: {e}")
        raise Exception(f"Failed to connect to Azure SQL Database: {e}")

def _get_sqlite_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _wrap_azure_sql_connection(conn):
    """Wrap Azure SQL connection to provide SQLite-like interface"""
    
    # Simple row wrapper that supports both index and key access
    class SimpleRow:
        def __init__(self, cursor, row):
            self.columns = [column[0] for column in cursor.description]
            self.values = list(row)
            self._dict = dict(zip(self.columns, self.values))
            
        def __getitem__(self, key):
            if isinstance(key, int):
                return self.values[key]
            return self._dict[key]
            
        def __contains__(self, key):
            return key in self._dict
            
        def keys(self):
            return self._dict.keys()
            
        def get(self, key, default=None):
            return self._dict.get(key, default)
    
    # Cursor wrapper that provides fetchone/fetchall with SimpleRow
    class AzureSQLCursorWrapper:
        def __init__(self, cursor):
            self._cursor = cursor
            
        def fetchone(self):
            row = self._cursor.fetchone()
            return SimpleRow(self._cursor, row) if row else None
            
        def fetchall(self):
            rows = self._cursor.fetchall()
            return [SimpleRow(self._cursor, row) for row in rows] if rows else []
            
        def __getattr__(self, name):
            # Delegate all other attributes to the original cursor
            return getattr(self._cursor, name)
    
    # Create wrapper class instead of modifying read-only attributes
    class AzureSQLConnectionWrapper:
        def __init__(self, connection):
            self._conn = connection
            
        def execute(self, query, params=()):
            cursor = self._conn.cursor()
            
            # Basic query conversions for common SQLite -> SQL Server differences
            if 'AUTOINCREMENT' in query.upper():
                query = query.replace('AUTOINCREMENT', 'IDENTITY(1,1)')
                query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'INT IDENTITY(1,1) PRIMARY KEY')
            
            cursor.execute(query, params)
            
            # Return wrapped cursor
            return AzureSQLCursorWrapper(cursor)
        
        def cursor(self):
            return AzureSQLCursorWrapper(self._conn.cursor())
        
        def commit(self):
            return self._conn.commit()
        
        def rollback(self):
            return self._conn.rollback()
        
        def close(self):
            return self._conn.close()
        
        def __getattr__(self, name):
            # Delegate any other attributes to the underlying connection
            return getattr(self._conn, name)
    
    logger.info("Azure SQL Database connection established with SQLite compatibility wrapper")
    return AzureSQLConnectionWrapper(conn)

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
        logger.error(f"Error recording failed attempt: {e}")
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
    expires_at = datetime.now() + timedelta(hours=24)
    session_table = get_session_table()  # Use centralized session table detection
    
    conn = get_db_connection()
    try:
        session_table = get_session_table()  # Use centralized session table detection
        
        # Invalidate old sessions for this user
        conn.execute(f'''
            UPDATE {session_table} 
            SET is_active = 0 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        # Create new session - Azure SQL has additional last_activity column
        if is_azure_sql():
            conn.execute(f'''
                INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at, last_activity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_token, user_id, ip_address, user_agent, expires_at, datetime.now()))
        else:
            conn.execute(f'''
                INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_token, user_id, ip_address, user_agent, expires_at))
        
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
        logger.error(f"Error creating session: {e}")
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
    session_table = get_session_table()  # Use centralized session table detection
    
    try:
        user_session = conn.execute(f'''
            SELECT s.*, u.username, u.level, u.points 
            FROM {session_table} s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = ?
        ''', (session_token, True)).fetchone()
        
        if user_session:
            # Update last activity if column exists (Azure SQL only)
            try:
                if is_azure_sql():
                    conn.execute(f'''
                        UPDATE {session_table} 
                        SET last_activity = ? 
                        WHERE session_token = ?
                    ''', (datetime.now(), session_token))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Could not update last_activity: {e}")
            
            user_result = {
                'id': user_session['user_id'],
                'username': user_session['username'],
                'level': user_session['level'],
                'points': user_session['points']
            }
            return user_result
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None
    finally:
        conn.close()

def invalidate_session(session_token):
    """Invalidate a user session"""
    conn = get_db_connection()
    session_table = get_session_table()  # Use centralized session table detection
    
    try:
        conn.execute(f'''
            UPDATE {session_table} 
            SET is_active = ? 
            WHERE session_token = ?
        ''', (False, session_token))
        conn.commit()
        
        # Remove from memory
        with session_lock:
            active_sessions.pop(session_token, None)
            
    except Exception as e:
        logger.error(f"Error invalidating session: {e}")
    finally:
        conn.close()

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
        logger.error(f"Error logging security event: {e}")
    finally:
        conn.close()

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

# Admin utility functions
def validate_admin_access():
    """Common admin access validation - returns user or redirects"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return None
    return user

def handle_db_operation(operation_func, success_message=None, error_message=None, redirect_route='admin_dashboard'):
    """Generic database operation handler with error management"""
    conn = get_db_connection()
    try:
        result = operation_func(conn)
        conn.commit()
        if success_message:
            flash(success_message, 'success')
        return result
    except Exception as e:
        conn.rollback()
        error_msg = error_message or f'Database operation failed: {str(e)}'
        flash(error_msg, 'error')
        logger.error(f"Database operation error: {e}")
        return None
    finally:
        conn.close()

def validate_course_data(form_data):
    """Validate course form data"""
    title = form_data.get('title', '').strip()
    description = form_data.get('description', '').strip()
    
    if not title or not description:
        return False, 'Title and description are required.'
    
    # Validate points
    try:
        points = int(form_data.get('points', 0)) if form_data.get('points') else 0
        if points < 0:
            return False, 'Points must be a positive number.'
    except ValueError:
        return False, 'Points must be a valid number.'
    
    # Validate URL if provided
    url = form_data.get('url', '').strip()
    if url and not url.startswith(('http://', 'https://')):
        return False, 'URL must start with http:// or https://'
    
    return True, None

def get_level_requirements():
    """Get current level point requirements from settings"""
    conn = get_db_connection()
    try:
        default_levels = {
            'Beginner': 0,
            'Learner': 100,
            'Intermediate': 300,
            'Advanced': 600,
            'Expert': 1000
        }
        
        try:
            # Try to load from database
            level_requirements = {}
            for level_name in default_levels.keys():
                setting_key = f"level_{level_name.lower()}_points"
                result = conn.execute(
                    'SELECT setting_value FROM app_settings WHERE setting_key = ?',
                    (setting_key,)
                ).fetchone()
                
                level_requirements[level_name] = int(result['setting_value']) if result else default_levels[level_name]
            
            return level_requirements
        except:
            # If settings table doesn't exist, return defaults
            return default_levels
    finally:
        conn.close()

def calculate_user_level(points):
    """Calculate user level based on current points"""
    level_requirements = get_level_requirements()
    
    # Sort levels by points in descending order
    sorted_levels = sorted(level_requirements.items(), key=lambda x: x[1], reverse=True)
    
    for level_name, required_points in sorted_levels:
        if points >= required_points:
            return level_name
    
    return 'Beginner'  # Default level

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

# User Learning Routes
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
        
        # Get level settings from database (use defaults if no settings table)
        try:
            level_settings = conn.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
            if not level_settings:
                raise Exception("No level settings found")
            level_mapping = {level['level_name']: level['points_required'] for level in level_settings}
        except:
            # Use default level mapping
            level_mapping = {
                'Beginner': 0,
                'Learner': 100,
                'Intermediate': 300,
                'Advanced': 600,
                'Expert': 1000
            }
        
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
    
    # Get user data
    conn = get_db_connection()
    try:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        
        # Try to get points log from database
        try:
            points_logs = conn.execute('''
                SELECT * FROM points_log 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user['id'],)).fetchall()
        except:
            points_logs = []
        
        # Basic user stats for display
        learning_count = conn.execute(
            'SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']
        
        completed_courses_count = conn.execute('''
            SELECT COUNT(*) as count FROM user_courses 
            WHERE user_id = ? AND completed = 1
        ''', (user['id'],)).fetchone()['count']
        
        level_info = {
            'next_level': None, 
            'points_to_next': 0, 
            'level_points': user_data['points'] if user_data else 0, 
            'progress_percentage': 0
        }
        
        return render_template('dashboard/profile.html', 
                             user=user_data,
                             learning_count=learning_count,
                             completed_courses_count=completed_courses_count,
                             level_info=level_info,
                             points_log=points_logs)
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
                SELECT c.*, uc.completion_date
                FROM courses c 
                INNER JOIN user_courses uc ON c.id = uc.course_id 
                WHERE uc.user_id = ? AND uc.completed = 1
                ORDER BY uc.completion_date DESC
            ''', (user['id'],)).fetchall()
        else:
            courses = conn.execute('''
                SELECT c.*
                FROM courses c 
                LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
                WHERE uc.completed IS NULL OR uc.completed = 0
                ORDER BY c.created_at DESC
            ''', (user['id'],)).fetchall()
        
        # Create CSV response
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        if course_type == 'completed':
            writer.writerow(['Title', 'Description', 'Provider', 'Level', 'URL', 'Completion Date'])
            for course in courses:
                writer.writerow([
                    course['title'],
                    course['description'] or '',
                    course['provider'] or '',
                    course['level'] or '',
                    course['url'] or '',
                    course.get('completion_date', '')
                ])
        else:
            writer.writerow(['Title', 'Description', 'Provider', 'Level', 'URL'])
            for course in courses:
                writer.writerow([
                    course['title'],
                    course['description'] or '',
                    course['provider'] or '',
                    course['level'] or '',
                    course['url'] or ''
                ])
        
        # Create response
        from flask import Response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course_type}_courses.csv'}
        )
    finally:
        conn.close()

# Course Completion Routes
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
                try:
                    log_completion_event(user['id'], course_id, course['title'])
                except:
                    pass  # Log completion but don't fail if logging fails
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            flash(f'Congratulations! You completed "{course["title"]}"!', 'success')
            try:
                log_completion_event(user['id'], course_id, course['title'])
            except:
                pass  # Log completion but don't fail if logging fails
    
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
                try:
                    log_completion_event(user['id'], course_id, course['title'])
                except:
                    pass  # Log completion but don't fail if logging fails
                return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
        else:
            # Insert new completion record
            conn.execute(
                'INSERT INTO user_courses (user_id, course_id, completed, completion_date) VALUES (?, ?, 1, CURRENT_TIMESTAMP)',
                (user['id'], course_id)
            )
            conn.commit()
            try:
                log_completion_event(user['id'], course_id, course['title'])
            except:
                pass  # Log completion but don't fail if logging fails
            return jsonify({'success': True, 'message': f'Completed "{course["title"]}"!'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

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
            try:
                log_security_event('completion_date_update', 
                                 f'Updated completion date for course {course_id} to {completion_date}',
                                 request.remote_addr, user_id)
            except:
                pass  # Log but don't fail if logging fails
        finally:
            conn.close()
    
    except Exception as e:
        flash(f'Error updating completion date: {str(e)}', 'error')
    
    return redirect(url_for('my_courses'))

def log_completion_event(user_id, course_id, course_title):
    """Log course completion event"""
    try:
        log_message = f'User {user_id} completed course {course_id}: {course_title}'
        log_security_event('course_completion', log_message, request.remote_addr, user_id)
    except Exception as e:
        try:
            log_security_event('course_completion_error', f'Error logging completion for user {user_id}, course {course_id}: {str(e)}', request.remote_addr, user_id)
        except:
            pass  # Silently ignore logging errors

@app.route('/debug-session')
def debug_session():
    """Debug endpoint to check session state"""
    try:
        session_token = session.get('session_token')
        debug_info = {
            'session_token': session_token,
            'is_azure_sql': is_azure_sql(),
            'session_table': get_session_table(),
            'all_env_vars': [k for k in os.environ.keys() if 'SQL' in k.upper() or 'CONNECTION' in k.upper()],
            'session_memory_count': len(active_sessions),
            'session_in_memory': session_token in active_sessions if session_token else False,
        }
        
        if session_token:
            # Try to get user info
            user = get_current_user()
            debug_info['current_user'] = user
        
        return debug_info
    except Exception as e:
        return {'error': str(e), 'traceback': str(e.__traceback__)}

@app.route('/test-environment-connection')
def test_environment_connection():
    """Test Azure SQL connection using environment variables"""
    try:
        # Check environment variables
        azure_server = os.environ.get('AZURE_SQL_SERVER')
        azure_database = os.environ.get('AZURE_SQL_DATABASE')
        azure_username = os.environ.get('AZURE_SQL_USERNAME')
        azure_password = os.environ.get('AZURE_SQL_PASSWORD')
        
        env_status = {
            'AZURE_SQL_SERVER': 'Set' if azure_server else 'Not set',
            'AZURE_SQL_DATABASE': 'Set' if azure_database else 'Not set',
            'AZURE_SQL_USERNAME': 'Set' if azure_username else 'Not set',
            'AZURE_SQL_PASSWORD': 'Set' if azure_password else 'Not set'
        }
        
        if not all([azure_server, azure_database, azure_username, azure_password]):
            return jsonify({
                'success': False,
                'error': 'Missing required Azure SQL environment variables',
                'environment_status': env_status,
                'next_steps': 'Set the missing environment variables in Azure App Service'
            })
        
        # Test connection using environment variables
        import pyodbc
        
        connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server=tcp:{azure_server},1433;"
            f"Database={azure_database};"
            f"Uid={azure_username};"
            f"Pwd={azure_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        # Check if user_sessions table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'user_sessions'
        """)
        user_sessions_exists = cursor.fetchone()[0] > 0
        
        # Test table access
        cursor.execute('SELECT COUNT(*) FROM user_sessions')
        sessions_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'environment_status': env_status,
            'connection_test': 'OK',
            'basic_query': result[0],
            'user_sessions_table_exists': user_sessions_exists,
            'sessions_count': sessions_count,
            'message': 'Successfully connected using environment variables!',
            'connection_method': 'environment_variables'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': f'Connection failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__,
            'environment_status': env_status if 'env_status' in locals() else 'Unknown'
        })

@app.route('/test-azure-connection-corrected')
def test_azure_connection_corrected():
    """Test Azure SQL connection with environment-based password"""
    try:
        import pyodbc
        
        # Build connection string using environment variables only
        azure_password = os.environ.get('AZURE_SQL_PASSWORD')
        if not azure_password:
            return jsonify({
                'error': 'AZURE_SQL_PASSWORD environment variable not set',
                'suggestion': 'Set the password in Azure App Service environment variables'
            })
        
        correct_connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:ai-learning-sql-centralus.database.windows.net,1433;Database=ai-learning-db;Uid=ailearningadmin;Pwd={azure_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        
        print("🔄 Testing Azure SQL with environment password...")
        
        # Try direct pyodbc connection
        conn = pyodbc.connect(correct_connection_string)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        # Test INFORMATION_SCHEMA access
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        
        # List all tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check if user_sessions table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'user_sessions'
        """)
        user_sessions_exists = cursor.fetchone()[0] > 0
        
        # Check if users table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'users'
        """)
        users_exists = cursor.fetchone()[0] > 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'connection_test': 'OK',
            'basic_query': result[0],
            'total_tables': table_count,
            'all_tables': tables,
            'user_sessions_table_exists': user_sessions_exists,
            'users_table_exists': users_exists,
            'message': 'Azure SQL connection successful with environment password!'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Azure SQL connection failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__
        })

@app.route('/test-azure-connection-updated')
def test_azure_connection_updated():
    """Test Azure SQL connection using environment variables"""
    if not is_azure_sql():
        return jsonify({
            'error': 'Azure SQL environment variables not set',
            'suggestion': 'Set AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD'
        })
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        # Test INFORMATION_SCHEMA access
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'connection_test': 'OK',
            'basic_query': result[0],
            'total_tables': table_count,
            'message': 'Azure SQL connection successful using environment variables'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Azure SQL connection failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__
        })

@app.route('/fix-azure-connection-and-create-tables')
def fix_azure_connection_and_create_tables():
    """Fix Azure SQL connection with environment password and create tables"""
    try:
        import pyodbc
        
        # Use environment variable for password
        azure_password = os.environ.get('AZURE_SQL_PASSWORD')
        if not azure_password:
            return jsonify({
                'error': 'AZURE_SQL_PASSWORD environment variable not set',
                'suggestion': 'Set the password in Azure App Service environment variables'
            })
        
        correct_connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:ai-learning-sql-centralus.database.windows.net,1433;Database=ai-learning-db;Uid=ailearningadmin;Pwd={azure_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        
        conn = pyodbc.connect(correct_connection_string)
        cursor = conn.cursor()
        
        # Check if user_sessions table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'user_sessions'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        # Create table if it doesn't exist
        if not table_exists:
            cursor.execute("""
                CREATE TABLE user_sessions (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL,
                    session_token NVARCHAR(255) NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT GETDATE(),
                    expires_at DATETIME NOT NULL,
                    is_active BIT DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
            message = '✅ user_sessions table created successfully'
        else:
            message = '✅ user_sessions table already exists'
        
        # Test table access
        cursor.execute('SELECT COUNT(*) FROM user_sessions')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': message,
            'table_existed': table_exists,
            'records_count': count,
            'connection_method': 'environment_password',
            'next_step': 'Azure SQL tables initialized successfully'
        })
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Table creation failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__
        })

@app.route('/test-admin-login-direct')
def test_admin_login_direct():
    """Test admin login process step by step"""
    try:
        # Step 1: Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({'step': 1, 'error': 'Database connection failed'})
        
        # Step 2: Check if admin user exists
        try:
            admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
            if not admin_user:
                return jsonify({'step': 2, 'error': 'Admin user not found'})
        except Exception as e:
            return jsonify({'step': 2, 'error': f'User lookup failed: {str(e)}'})
        
        # Step 3: Test password verification
        from werkzeug.security import check_password_hash
        test_password = os.environ.get('ADMIN_PASSWORD')
        if not test_password:
            return jsonify({'step': 3, 'error': 'ADMIN_PASSWORD environment variable not set'})
        
        try:
            password_valid = check_password_hash(admin_user['password_hash'], test_password)
            if not password_valid:
                return jsonify({'step': 3, 'error': 'Password verification failed'})
        except Exception as e:
            return jsonify({'step': 3, 'error': f'Password check failed: {str(e)}'})
        
        # Step 4: Test session creation
        try:
            session_token = create_user_session(
                admin_user['id'],
                '127.0.0.1',  # test IP
                'Test User Agent'
            )
            if not session_token:
                return jsonify({'step': 4, 'error': 'Session creation failed'})
        except Exception as e:
            return jsonify({'step': 4, 'error': f'Session creation error: {str(e)}'})
        
        # Step 5: Test session retrieval
        try:
            session_table = get_session_table()  # Use centralized session table detection
            
            user_session = conn.execute(f'''
                SELECT s.*, u.username, u.level, u.points 
                FROM {session_table} s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.session_token = ? AND s.is_active = ?
            ''', (session_token, True)).fetchone()
            
            if not user_session:
                return jsonify({'step': 5, 'error': f'Session not found in {session_table}'})
                
        except Exception as e:
            return jsonify({'step': 5, 'error': f'Session retrieval failed: {str(e)}'})
        
        # Step 6: Clean up test session
        try:
            conn.execute(f'''
                DELETE FROM {session_table} 
                WHERE session_token = ?
            ''', (session_token,))
            conn.commit()
        except Exception as e:
            # Non-critical error
            pass
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'All login steps completed successfully',
            'admin_user_id': admin_user['id'],
            'session_table_used': session_table,
            'session_token_created': session_token[:10] + '...',
            'user_level': admin_user.get('level', 'N/A'),
            'is_azure_sql': is_azure_sql()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/admin-test')
def admin_test():
    """Simple admin test to debug issues"""
    try:
        # Test 1: Session check
        session_token = session.get('session_token')
        if not session_token:
            return "❌ No session token"
        
        # Test 2: Memory session check
        with session_lock:
            if session_token not in active_sessions:
                return "❌ Session not in memory"
        
        # Test 3: Database connection
        try:
            conn = get_db_connection()
            if not conn:
                return "❌ No database connection"
        except Exception as e:
            return f"❌ Database connection error: {e}"
        
        # Test 4: Simple query
        try:
            result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
            user_count = result[0] if result else 0
        except Exception as e:
            return f"❌ Query error: {e}"
        finally:
            conn.close()
        
        # Test 5: Admin user check
        try:
            conn = get_db_connection()
            session_table = get_session_table()  # Use centralized session table detection
            
            user_session = conn.execute(f'''
                SELECT s.user_id, u.username 
                FROM {session_table} s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.session_token = ? AND s.is_active = ?
            ''', (session_token, True)).fetchone()
            
            if not user_session:
                return f"❌ No user session found in {session_table}"
            
            username = user_session[1] if hasattr(user_session, '__getitem__') else user_session.username
            
            if username != 'admin':
                return f"❌ User is not admin: {username}"
                
            conn.close()
            return f"✅ All tests passed! User count: {user_count}, Admin user: {username}"
            
        except Exception as e:
            return f"❌ Admin check error: {e}"
        
    except Exception as e:
        return f"❌ Critical error: {e}"

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    try:
        # Simple session check first
        session_token = session.get('session_token')
        if not session_token:
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('login'))
        
        # Check memory session first (faster)
        with session_lock:
            if session_token not in active_sessions:
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('login'))
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'error')
            return redirect(url_for('login'))
        
        try:
            # Check if user exists in database - use centralized session table detection
            user_data = None
            session_table = get_session_table()
            
            try:
                user_session = conn.execute(f'''
                    SELECT s.user_id, u.username, u.level, u.points 
                    FROM {session_table} s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE s.session_token = ? AND s.is_active = ?
                ''', (session_token, True)).fetchone()
                
                if user_session:
                    user_data = {
                        'id': user_session[0],
                        'username': user_session[1],
                        'level': user_session[2],
                        'points': user_session[3]
                    }
            except Exception as db_error:
                logger.error(f"Database lookup error: {db_error}")
                # Fallback: check if username is admin based on session memory
                session_data = active_sessions.get(session_token, {})
                if session_data:
                    # Try direct user lookup
                    try:
                        user_record = conn.execute('SELECT id, username, level, points FROM users WHERE username = ?', ('admin',)).fetchone()
                        if user_record:
                            user_data = {
                                'id': user_record[0],
                                'username': user_record[1],
                                'level': user_record[2],
                                'points': user_record[3]
                            }
                    except Exception as user_error:
                        logger.error(f"User lookup error: {user_error}")
            
            # Check if user is admin
            if not user_data or user_data.get('username') != 'admin':
                flash('Admin privileges required.', 'error')
                return redirect(url_for('login'))
            
            # Get basic statistics for admin dashboard
            try:
                result = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
                user_count = result[0] if hasattr(result, '__getitem__') else result
                if hasattr(result, 'keys') and 'count' in result:
                    user_count = result['count']
            except Exception as e:
                logger.error(f"Error getting user count: {e}")
                user_count = 0
                
            try:
                result = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()
                course_count = result[0] if hasattr(result, '__getitem__') else result
                if hasattr(result, 'keys') and 'count' in result:
                    course_count = result['count']
            except Exception as e:
                logger.error(f"Error getting course count: {e}")
                course_count = 0
                
            try:
                result = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()
                learning_count = result[0] if hasattr(result, '__getitem__') else result
                if hasattr(result, 'keys') and 'count' in result:
                    learning_count = result['count']
            except Exception as e:
                logger.error(f"Error getting learning count: {e}")
                learning_count = 0
            
            # Get recent users
            recent_users = []
            try:
                recent_users = conn.execute('''
                    SELECT username, level, points, created_at 
                    FROM users 
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''').fetchall()
            except Exception as e:
                logger.error(f"Error getting recent users: {e}")
            
            return render_template('admin/index.html',
                                 total_users=user_count,
                                 total_courses=course_count,
                                 total_learnings=learning_count,
                                 recent_users=recent_users)
        
        except Exception as e:
            logger.error(f"Error in admin dashboard: {e}")
            flash('Database error occurred. Please check the logs.', 'error')
            return redirect(url_for('login'))
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Critical error in admin dashboard: {e}")
        flash('System error. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/initialize-azure-database-complete')
def initialize_azure_database_complete():
    """Initialize all missing tables in Azure SQL database"""
    try:
        import pyodbc
        
        # Use environment variables for connection
        azure_password = os.environ.get('AZURE_SQL_PASSWORD')
        if not azure_password:
            return jsonify({
                'error': 'AZURE_SQL_PASSWORD environment variable not set',
                'suggestion': 'Set the password in Azure App Service environment variables'
            })
        
        connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:ai-learning-sql-centralus.database.windows.net,1433;Database=ai-learning-db;Uid=ailearningadmin;Pwd={azure_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        results = []
        
        # Create users table
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users')
                BEGIN
                    CREATE TABLE users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username NVARCHAR(255) UNIQUE NOT NULL,
                        password_hash NVARCHAR(255) NOT NULL,
                        level NVARCHAR(50) DEFAULT 'Beginner',
                        points INT DEFAULT 0,
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME DEFAULT GETDATE()
                    )
                END
            """)
            conn.commit()
            results.append("✅ users table created/verified")
        except Exception as e:
            results.append(f"❌ users table error: {str(e)}")
        
        # Create user_sessions table
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'user_sessions')
                BEGIN
                    CREATE TABLE user_sessions (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        session_token NVARCHAR(255) UNIQUE NOT NULL,
                        user_id INT NOT NULL,
                        ip_address NVARCHAR(45),
                        user_agent NVARCHAR(MAX),
                        created_at DATETIME DEFAULT GETDATE(),
                        expires_at DATETIME NOT NULL,
                        is_active BIT DEFAULT 1,
                        last_activity DATETIME DEFAULT GETDATE(),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                END
            """)
            conn.commit()
            results.append("✅ user_sessions table created/verified")
        except Exception as e:
            results.append(f"❌ user_sessions table error: {str(e)}")
        
        # Create learning_entries table
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'learning_entries')
                BEGIN
                    CREATE TABLE learning_entries (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_id INT NOT NULL,
                        title NVARCHAR(255) NOT NULL,
                        description NVARCHAR(MAX),
                        difficulty NVARCHAR(50),
                        hours_spent FLOAT,
                        completed_date DATE,
                        created_at DATETIME DEFAULT GETDATE(),
                        date_added DATETIME DEFAULT GETDATE(),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                END
            """)
            conn.commit()
            results.append("✅ learning_entries table created/verified")
        except Exception as e:
            results.append(f"❌ learning_entries table error: {str(e)}")
        
        # Create courses table
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'courses')
                BEGIN
                    CREATE TABLE courses (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        title NVARCHAR(255) NOT NULL,
                        description NVARCHAR(MAX),
                        difficulty NVARCHAR(50),
                        duration_hours FLOAT,
                        url NVARCHAR(MAX),
                        category NVARCHAR(100),
                        level NVARCHAR(50) DEFAULT 'Beginner',
                        created_at DATETIME DEFAULT GETDATE()
                    )
                END
            """)
            conn.commit()
            results.append("✅ courses table created/verified")
        except Exception as e:
            results.append(f"❌ courses table error: {str(e)}")
        
        # Create user_courses table
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'user_courses')
                BEGIN
                    CREATE TABLE user_courses (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_id INT NOT NULL,
                        course_id INT NOT NULL,
                        completed BIT DEFAULT 0,
                        completed_date DATETIME,
                        created_at DATETIME DEFAULT GETDATE(),
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (course_id) REFERENCES courses(id),
                        UNIQUE(user_id, course_id)
                    )
                END
            """)
            conn.commit()
            results.append("✅ user_courses table created/verified")
        except Exception as e:
            results.append(f"❌ user_courses table error: {str(e)}")
        
        # Create security_logs table
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'security_logs')
                BEGIN
                    CREATE TABLE security_logs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        ip_address NVARCHAR(45),
                        username NVARCHAR(255),
                        action NVARCHAR(100),
                        success BIT,
                        user_agent NVARCHAR(MAX),
                        created_at DATETIME DEFAULT GETDATE()
                    )
                END
            """)
            conn.commit()
            results.append("✅ security_logs table created/verified")
        except Exception as e:
            results.append(f"❌ security_logs table error: {str(e)}")
        
        # Create admin user if it doesn't exist
        try:
            from werkzeug.security import generate_password_hash
            
            # Check if admin user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            admin_exists = cursor.fetchone()[0] > 0
            
            if not admin_exists:
                admin_password = os.environ.get('ADMIN_PASSWORD')
                if not admin_password:
                    results.append("❌ ADMIN_PASSWORD environment variable not set - cannot create admin user")
                    return results
                password_hash = generate_password_hash(admin_password)
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, level, points)
                    VALUES (?, ?, ?, ?)
                """, ('admin', password_hash, 'Expert', 1000))
                conn.commit()
                results.append("✅ Admin user created successfully")
            else:
                results.append("✅ Admin user already exists")
        except Exception as e:
            results.append(f"❌ Admin user creation error: {str(e)}")
        
        # Final verification - list all tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        all_tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Database initialization completed',
            'results': results,
            'all_tables': all_tables,
            'total_tables': len(all_tables)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': f'Database initialization failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__
        })

@app.route('/create-admin-emergency')
def create_admin_emergency():
    """Emergency admin creation endpoint"""
    conn = get_db_connection()
    try:
        # Check if admin user already exists
        admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        
        if admin_user:
            return "<h2>✅ Admin user already exists!</h2><p>The admin user is already created in the database.</p><a href='/login'>Go to Login</a>"
        
        # Create admin user
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Expert', 1000, datetime.now()))
        conn.commit()
        
        return "<h2>✅ Admin user created successfully!</h2><p>You can now log in with username 'admin' and your password.</p><a href='/login'>Go to Login</a>"
        
    except Exception as e:
        return f"<h2>❌ Error creating admin user:</h2><pre>{e}</pre><p><a href='/'>Back to Home</a></p>"
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
        
        # Get activity statistics (last 7 days) - handle missing table gracefully
        activity_stats = []
        try:
            activity_stats = conn.execute('''
                SELECT activity_type, COUNT(*) as count
                FROM session_activity 
                WHERE datetime(timestamp) >= datetime('now', '-7 days')
                GROUP BY activity_type
                ORDER BY count DESC
            ''').fetchall()
        except:
            pass  # session_activity table might not exist
        
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
        events = []
        try:
            events = conn.execute('''
                SELECT * FROM security_events 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''').fetchall()
        except:
            pass  # security_events table might not exist
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

@app.route('/admin/settings', methods=['GET', 'POST'])
@require_admin
def admin_settings():
    """Admin settings page with level management"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle settings update
        try:
            # Get level point requirements from form
            levels_data = [
                {'level_name': 'Beginner', 'points_required': int(request.form.get('beginner_points', 0))},
                {'level_name': 'Learner', 'points_required': int(request.form.get('learner_points', 100))},
                {'level_name': 'Intermediate', 'points_required': int(request.form.get('intermediate_points', 300))},
                {'level_name': 'Advanced', 'points_required': int(request.form.get('advanced_points', 600))},
                {'level_name': 'Expert', 'points_required': int(request.form.get('expert_points', 1000))}
            ]
            
            # Validate that levels are in ascending order
            for i in range(1, len(levels_data)):
                if levels_data[i]['points_required'] <= levels_data[i-1]['points_required']:
                    flash('Level point requirements must be in ascending order.', 'error')
                    return redirect(url_for('admin_settings'))
            
            # Store settings in a simple way (you can enhance this with a proper settings table later)
            conn = get_db_connection()
            try:
                # Create settings table if it doesn't exist
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS app_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT UNIQUE NOT NULL,
                        setting_value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Update level settings
                for level_data in levels_data:
                    setting_key = f"level_{level_data['level_name'].lower()}_points"
                    conn.execute('''
                        INSERT OR REPLACE INTO app_settings (setting_key, setting_value, updated_at)
                        VALUES (?, ?, datetime('now'))
                    ''', (setting_key, str(level_data['points_required'])))
                
                conn.commit()
                flash('Settings updated successfully!', 'success')
                
                # Update user levels based on new requirements
                update_all_user_levels(conn, levels_data)
                
            except Exception as e:
                conn.rollback()
                flash(f'Error updating settings: {str(e)}', 'error')
                logger.error(f"Settings update error: {e}")
            finally:
                conn.close()
                
        except ValueError:
            flash('Invalid point values provided.', 'error')
        
        return redirect(url_for('admin_settings'))
    
    # GET request - load current settings
    conn = get_db_connection()
    try:
        # Default level settings
        default_levels = [
            {'level_name': 'Beginner', 'points_required': 0},
            {'level_name': 'Learner', 'points_required': 100},
            {'level_name': 'Intermediate', 'points_required': 300},
            {'level_name': 'Advanced', 'points_required': 600},
            {'level_name': 'Expert', 'points_required': 1000}
        ]
        
        # Try to load from database
        try:
            level_settings = []
            for level in default_levels:
                setting_key = f"level_{level['level_name'].lower()}_points"
                result = conn.execute(
                    'SELECT setting_value FROM app_settings WHERE setting_key = ?',
                    (setting_key,)
                ).fetchone()
                
                points_required = int(result['setting_value']) if result else level['points_required']
                level_settings.append({
                    'level_name': level['level_name'],
                    'points_required': points_required
                })
        except:
            # If settings table doesn't exist, use defaults
            level_settings = default_levels
        
        return render_template('admin/settings.html', 
                                level_settings=level_settings,
                                is_azure_sql=is_azure_sql(),
                                debug_mode=app.debug)
        
    finally:
        conn.close()

def update_all_user_levels(conn, levels_data):
    """Update all user levels based on new point requirements"""
    try:
        users = conn.execute('SELECT id, points FROM users').fetchall()
        
        for user in users:
            user_points = user['points'] or 0
            new_level = 'Beginner'
            
            # Determine new level based on points
            for level_data in reversed(levels_data):
                if user_points >= level_data['points_required']:
                    new_level = level_data['level_name']
                    break
            
            # Update user level
            conn.execute(
                'UPDATE users SET level = ?, level_updated_at = datetime("now") WHERE id = ?',
                (new_level, user['id'])
            )
        
        conn.commit()
        logger.info(f"Updated levels for {len(users)} users based on new requirements")
        
    except Exception as e:
        logger.error(f"Error updating user levels: {e}")

@app.route('/admin/change-password')
def admin_change_password():
    """Admin password change page"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Password change page (placeholder implementation)
    return render_template('admin/change_password.html')

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

@app.route('/admin/add-course', methods=['GET', 'POST'])
@require_admin
def admin_add_course():
    """Add a new course (admin only)"""
    if request.method == 'POST':
        # Collect form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        source = request.form.get('source', '').strip()
        url = request.form.get('url', '').strip() or None
        level = request.form.get('level', '').strip()
        category = request.form.get('category', '').strip() or None
        points = request.form.get('points', 0)
        
        # Basic validation
        if not title or not description:
            flash('Title and description are required.', 'error')
            return render_template('admin/add_course.html')
        
        try:
            points = int(points) if points else 0
        except ValueError:
            points = 0
        
        # Auto-calculate level based on points if not provided
        if not level:
            if points < 150:
                level = 'Beginner'
            elif points < 250:
                level = 'Intermediate'
            else:
                level = 'Advanced'
        
        conn = get_db_connection()
        try:
            # Check for duplicates
            existing = conn.execute(
                'SELECT id FROM courses WHERE title = ? AND url = ?', 
                (title, url)
            ).fetchone()
            if existing:
                flash('A course with this title and URL already exists.', 'error')
                return render_template('admin/add_course.html')
            
            # Insert the course
            conn.execute('''
                INSERT INTO courses 
                (title, description, url, link, source, level, points, category, created_at, url_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ''', (title, description, url, url, source, level, points, category, 'Pending'))
            conn.commit()
            
            flash(f'Course "{title}" added successfully!', 'success')
            return redirect(url_for('admin_courses'))
        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin/add_course.html')

@app.route('/admin/reset-all-user-passwords', methods=['POST'])
@require_admin
def admin_reset_all_user_passwords():
    """Reset all user passwords (admin only)"""
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    confirmation = request.form.get('reset_all_confirmation')
    
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
        flash(f'Successfully reset passwords for {updated_count} users.', 'success')
        
    except Exception as e:
        flash(f'Error resetting passwords: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reset-user-password', methods=['POST'])
@require_admin
def admin_reset_user_password():
    """Reset individual user password (admin only)"""
    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')
    
    if not user_id or not new_password:
        flash('User ID and new password are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        # Check if user exists
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update user password
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (hashed_password, user_id)
        )
        conn.commit()
        
        flash(f'Password reset successfully for user "{user["username"]}".', 'success')
        
    except Exception as e:
        flash(f'Error resetting password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

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
        # Delete courses
        for course_id in course_ids:
            result = conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            if result.rowcount > 0:
                deleted_count += 1
        
        conn.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} course(s)!', 'success')
        else:
            flash('No courses were deleted.', 'warning')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting courses: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/toggle-user-status/<int:user_id>', methods=['POST'])
@require_admin
def admin_toggle_user_status(user_id):
    """Toggle user status between active and inactive"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Check if user exists and get current status
        user_record = conn.execute('SELECT id, username, status FROM users WHERE id = ? AND username != ?', (user_id, 'admin')).fetchone()
        
        if not user_record:
            flash('User not found or cannot modify admin user.', 'error')
            return redirect(url_for('admin_users'))
        
        # Toggle status
        current_status = user_record.get('status', 'active')
        new_status = 'inactive' if current_status == 'active' else 'active'
        
        # Update user status
        conn.execute('UPDATE users SET status = ?, updated_at = datetime("now") WHERE id = ?', (new_status, user_id))
        
        # If deactivating user, invalidate their sessions
        if new_status == 'inactive':
            session_table = get_session_table()
            conn.execute(f'UPDATE {session_table} SET is_active = ? WHERE user_id = ?', (False, user_id))
        
        conn.commit()
        
        status_text = "activated" if new_status == 'active' else "deactivated"
        flash(f'User "{user_record["username"]}" has been {status_text}.', 'success')
        
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
        logger.error(f"Error toggling user status: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@require_admin
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Check if user exists and is not admin
        user_record = conn.execute('SELECT id, username FROM users WHERE id = ? AND username != ?', (user_id, 'admin')).fetchone()
        
        if not user_record:
            flash('User not found or cannot delete admin user.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user_record['username']
        
        # Delete user's sessions first (to maintain referential integrity)
        session_table = get_session_table()
        conn.execute(f'DELETE FROM {session_table} WHERE user_id = ?', (user_id,))
        
        # Delete user's learning entries
        conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        
        # Delete user's course associations if table exists
        try:
            conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        except:
            pass  # Table might not exist
        
        # Finally delete the user
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        flash(f'User "{username}" has been permanently deleted.', 'success')
        
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
        logger.error(f"Error deleting user: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

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

# Initialize database on startup
logger.info("Initializing AI Learning Tracker...")
initialize_database()

@app.route('/admin/course-configs')
@require_admin
def admin_course_configs():
    """Admin route to manage course configurations"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Get course configuration statistics
        total_courses = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        published_courses = conn.execute('SELECT COUNT(*) as count FROM courses WHERE status = "published"').fetchone()['count']
        draft_courses = conn.execute('SELECT COUNT(*) as count FROM courses WHERE status = "draft"').fetchone()['count']
        
        # Get recent course activities
        recent_courses = conn.execute('''
            SELECT title, status, created_at, points 
            FROM courses 
            ORDER BY created_at DESC 
            LIMIT 10
        ''').fetchall()
        
        stats = {
            'total_courses': total_courses,
            'published_courses': published_courses,
            'draft_courses': draft_courses,
            'recent_courses': recent_courses
        }
        
        return render_template('admin/course_configs.html', stats=stats)
    except Exception as e:
        flash(f'Error loading course configurations: {str(e)}', 'error')
        logger.error(f"Course configs error: {e}")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/admin/populate-ai-courses', methods=['GET', 'POST'])
@require_admin
def admin_populate_ai_courses():
    """Admin route to populate AI courses"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        def populate_courses(conn):
            # Sample AI courses to populate
            ai_courses = [
                {
                    'title': 'Introduction to Machine Learning',
                    'description': 'Learn the fundamentals of machine learning algorithms and applications.',
                    'points': 100,
                    'difficulty': 'Beginner',
                    'category': 'Machine Learning',
                    'url': 'https://docs.microsoft.com/learn/paths/intro-to-ml-with-python/',
                    'status': 'published'
                },
                {
                    'title': 'Deep Learning with PyTorch',
                    'description': 'Master deep learning concepts using PyTorch framework.',
                    'points': 150,
                    'difficulty': 'Intermediate',
                    'category': 'Deep Learning',
                    'url': 'https://docs.microsoft.com/learn/paths/pytorch-fundamentals/',
                    'status': 'published'
                },
                {
                    'title': 'Natural Language Processing',
                    'description': 'Explore NLP techniques for text analysis and language understanding.',
                    'points': 120,
                    'difficulty': 'Intermediate',
                    'category': 'NLP',
                    'url': 'https://docs.microsoft.com/learn/paths/explore-natural-language-processing/',
                    'status': 'published'
                },
                {
                    'title': 'Computer Vision Fundamentals',
                    'description': 'Learn image processing and computer vision algorithms.',
                    'points': 130,
                    'difficulty': 'Intermediate',
                    'category': 'Computer Vision',
                    'url': 'https://docs.microsoft.com/learn/paths/computer-vision-microsoft-cognitive-toolkit/',
                    'status': 'published'
                },
                {
                    'title': 'AI Ethics and Responsible AI',
                    'description': 'Understanding ethical considerations in AI development and deployment.',
                    'points': 80,
                    'difficulty': 'Beginner',
                    'category': 'AI Ethics',
                    'url': 'https://docs.microsoft.com/learn/paths/responsible-ai-principles/',
                    'status': 'published'
                }
            ]
            
            count = 0
            for course in ai_courses:
                # Check if course already exists
                existing = conn.execute('SELECT id FROM courses WHERE title = ?', (course['title'],)).fetchone()
                if not existing:
                    conn.execute('''
                        INSERT INTO courses (title, description, points, difficulty, category, url, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ''', (course['title'], course['description'], course['points'], 
                          course['difficulty'], course['category'], course['url'], course['status']))
                    count += 1
            
            return count
        
        result = handle_db_operation(
            populate_courses,
            success_message=None,  # We'll set custom message
            error_message='Failed to populate AI courses'
        )
        
        if result is not None:
            flash(f'Successfully added {result} AI courses to the database.', 'success')
        
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/populate_ai_courses.html')

@app.route('/admin/search-and-import-courses', methods=['GET', 'POST'])
@require_admin
def admin_search_and_import_courses():
    """Admin route to search and import courses"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        
        if not search_query:
            flash('Please enter a search query.', 'error')
            return render_template('admin/search_import_courses.html')
        
        # Mock search results (in production, this would integrate with Microsoft Learn API)
        mock_results = [
            {
                'title': f'Advanced {search_query} Concepts',
                'description': f'Deep dive into {search_query} with practical examples.',
                'points': 120,
                'difficulty': 'Advanced',
                'category': search_query.title(),
                'url': f'https://docs.microsoft.com/learn/paths/{search_query.lower()}-advanced/',
                'provider': 'Microsoft Learn'
            },
            {
                'title': f'{search_query} for Beginners',
                'description': f'Introduction to {search_query} fundamentals.',
                'points': 80,
                'difficulty': 'Beginner',
                'category': search_query.title(),
                'url': f'https://docs.microsoft.com/learn/paths/{search_query.lower()}-basics/',
                'provider': 'Microsoft Learn'
            }
        ]
        
        return render_template('admin/search_import_courses.html', 
                             search_query=search_query, 
                             search_results=mock_results)
    
    return render_template('admin/search_import_courses.html')

@app.route('/admin/edit-course/<int:course_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_course(course_id):
    """Admin route to edit a specific course"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('admin_courses'))
        
        if request.method == 'POST':
            # Get form data with template field names
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            points = request.form.get('points', 0)
            source = request.form.get('source', '').strip()
            level = request.form.get('level', '').strip()
            link = request.form.get('link', '').strip()
            
            # Basic validation
            if not title:
                flash('Course title is required.', 'error')
                return render_template('admin/edit_course.html', course=course)
                
            if not link:
                flash('Course link is required.', 'error')
                return render_template('admin/edit_course.html', course=course)
            
            # Validate points
            try:
                points = int(points) if points else 0
                if points < 0:
                    flash('Points must be a positive number.', 'error')
                    return render_template('admin/edit_course.html', course=course)
            except ValueError:
                flash('Points must be a valid number.', 'error')
                return render_template('admin/edit_course.html', course=course)
            
            def update_course(conn):
                # Check if courses table has the expected columns
                columns = [col[1] for col in conn.execute('PRAGMA table_info(courses)').fetchall()]
                
                if 'source' in columns and 'level' in columns and 'link' in columns:
                    # Use template field names if they exist in database
                    conn.execute('''
                        UPDATE courses 
                        SET title = ?, description = ?, points = ?, source = ?, 
                            level = ?, link = ?, updated_at = datetime('now')
                        WHERE id = ?
                    ''', (title, description, points, source, level, link, course_id))
                else:
                    # Fallback to our field names, mapping template fields
                    conn.execute('''
                        UPDATE courses 
                        SET title = ?, description = ?, points = ?, difficulty = ?, 
                            category = ?, url = ?, updated_at = datetime('now')
                        WHERE id = ?
                    ''', (title, description, points, level, source, link, course_id))
                return True
            
            result = handle_db_operation(
                update_course,
                success_message='Course updated successfully!',
                error_message='Failed to update course'
            )
            
            if result:
                return redirect(url_for('admin_courses'))
        
        return render_template('admin/edit_course.html', course=course)
        
    except Exception as e:
        flash(f'Error loading course: {str(e)}', 'error')
        logger.error(f"Edit course error: {e}")
        return redirect(url_for('admin_courses'))
    finally:
        conn.close()

@app.route('/admin/delete-course/<int:course_id>', methods=['POST'])
@require_admin
def admin_delete_course(course_id):
    """Admin route to delete a specific course"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    def delete_course(conn):
        # Check if course exists
        course = conn.execute('SELECT title FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            return False, 'Course not found'
        
        # Delete course
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        return True, course['title']
    
    result = handle_db_operation(
        lambda conn: delete_course(conn),
        success_message=None,  # Custom message
        error_message='Failed to delete course'
    )
    
    if result and result[0]:
        flash(f'Course "{result[1]}" deleted successfully!', 'success')
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/reports')
@require_admin
def admin_reports():
    """Admin reports dashboard"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        # Generate comprehensive reports
        reports = {
            'user_stats': conn.execute('''
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN last_login_at > datetime('now', '-30 days') THEN 1 END) as active_users,
                    COUNT(CASE WHEN created_at > datetime('now', '-7 days') THEN 1 END) as new_users
                FROM users
            ''').fetchone(),
            
            'learning_stats': conn.execute('''
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT user_id) as users_with_entries,
                    AVG(CAST(rating as FLOAT)) as avg_rating,
                    SUM(time_spent) as total_time_spent
                FROM learning_entries
            ''').fetchone(),
            
            'course_stats': conn.execute('''
                SELECT 
                    COUNT(*) as total_courses,
                    COUNT(CASE WHEN status = 'published' THEN 1 END) as published_courses,
                    AVG(points) as avg_points
                FROM courses
            ''').fetchone(),
            
            'top_learners': conn.execute('''
                SELECT u.username, u.level, COUNT(le.id) as entry_count, SUM(le.time_spent) as total_time
                FROM users u
                LEFT JOIN learning_entries le ON u.id = le.user_id
                WHERE u.username != 'admin'
                GROUP BY u.id
                ORDER BY entry_count DESC, total_time DESC
                LIMIT 10
            ''').fetchall()
        }
        
        return render_template('admin/reports.html', reports=reports)
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'error')
        logger.error(f"Reports error: {e}")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/admin/reports/upload-reports')
@require_admin
def admin_reports_upload_reports_list():
    """Admin route for upload reports list (alias for admin_reports.upload_reports_list)"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    # This is a placeholder for upload reports functionality
    # In a full implementation, this would show upload/import reports
    flash('Upload reports feature is under development.', 'info')
    return redirect(url_for('admin_reports'))

@app.route('/admin/reports/purge', methods=['POST'])
@require_admin
def admin_reports_purge_reports():
    """Admin route to purge old reports (alias for admin_reports.purge_reports)"""
    user = validate_admin_access()
    if not user:
        return redirect(url_for('dashboard'))
    
    # This is a placeholder for purging old reports
    # In a full implementation, this would clean up old log/report data
    flash('Report purge functionality is under development.', 'info')
    return redirect(url_for('admin_reports'))

# Create Blueprint-style route aliases for template compatibility
app.add_url_rule('/admin/reports/upload-reports-list', 'admin_reports.upload_reports_list', admin_reports_upload_reports_list, methods=['GET'])
app.add_url_rule('/admin/reports/purge-reports', 'admin_reports.purge_reports', admin_reports_purge_reports, methods=['POST'])

@app.route('/debug/env')
def debug_environment():
    """Debug endpoint to check environment variables in Azure"""
    # Allow access to check environment variables without admin session
    # This is safe as we only show whether variables are set, not their values
    
    # Check key environment variables
    env_info = {
        'environment': os.environ.get('ENV', 'not_set'),
        'azure_sql_server': 'SET' if os.environ.get('AZURE_SQL_SERVER') else 'NOT_SET',
        'azure_sql_database': 'SET' if os.environ.get('AZURE_SQL_DATABASE') else 'NOT_SET', 
        'azure_sql_username': 'SET' if os.environ.get('AZURE_SQL_USERNAME') else 'NOT_SET',
        'azure_sql_password_set': 'SET' if os.environ.get('AZURE_SQL_PASSWORD') else 'NOT_SET',
        'admin_password_set': 'SET' if os.environ.get('ADMIN_PASSWORD') else 'NOT_SET',
        'website_site_name': os.environ.get('WEBSITE_SITE_NAME', 'not_set'),
        'pythonpath': os.environ.get('PYTHONPATH', 'not_set'),
        'total_env_vars': len(os.environ),
        'is_azure_env': 'SET' if os.environ.get('WEBSITE_SITE_NAME') else 'NOT_SET'
    }
    
    return jsonify(env_info)

@app.route('/debug/db-test')
def debug_database_test():
    """Test database connection and return detailed error information"""
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('ENV', 'not_set'),
        'tests': []
    }
    
    # Test 1: Check if Azure SQL variables are set
    test1 = {
        'name': 'Environment Variables',
        'status': 'unknown',
        'details': {}
    }
    
    if is_azure_sql():
        test1['status'] = 'PASS'
        test1['details'] = {'message': 'All Azure SQL environment variables are set'}
    else:
        test1['status'] = 'FAIL'
        test1['details'] = {'message': 'Missing Azure SQL environment variables'}
    
    result['tests'].append(test1)
    
    # Test 2: Try to get database connection
    test2 = {
        'name': 'Database Connection',
        'status': 'unknown',
        'details': {}
    }
    
    try:
        conn = get_db_connection()
        if conn:
            test2['status'] = 'PASS'
            test2['details'] = {'message': 'Database connection successful'}
            
            # Test 3: Try a simple query
            test3 = {
                'name': 'Database Query',
                'status': 'unknown',
                'details': {}
            }
            
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                test3['status'] = 'PASS'
                test3['details'] = {'message': f'Query successful, {user_count} users found'}
                cursor.close()
            except Exception as e:
                test3['status'] = 'FAIL'
                test3['details'] = {'error': str(e), 'type': type(e).__name__}
            
            result['tests'].append(test3)
            conn.close()
        else:
            test2['status'] = 'FAIL'
            test2['details'] = {'message': 'Failed to get database connection'}
            
    except Exception as e:
        test2['status'] = 'FAIL'
        test2['details'] = {'error': str(e), 'type': type(e).__name__}
    
    result['tests'].append(test2)
    
    return jsonify(result)

@app.route('/debug/odbc-simple')
def debug_odbc_simple():
    """Simple ODBC check that won't hang the app"""
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('ENV', 'not_set'),
    }
    
    try:
        # Test 1: Can we import pyodbc?
        try:
            import pyodbc
            result['pyodbc_import'] = 'SUCCESS'
            result['pyodbc_version'] = pyodbc.version
        except ImportError as e:
            result['pyodbc_import'] = 'FAILED'
            result['import_error'] = str(e)
            return jsonify(result)
        
        # Test 2: Can we create a connection string?
        try:
            azure_server = os.environ.get('AZURE_SQL_SERVER')
            azure_database = os.environ.get('AZURE_SQL_DATABASE')
            azure_username = os.environ.get('AZURE_SQL_USERNAME')
            azure_password = os.environ.get('AZURE_SQL_PASSWORD')
            
            connection_string = (
                f"Driver={{ODBC Driver 17 for SQL Server}};"
                f"Server=tcp:{azure_server},1433;"
                f"Database={azure_database};"
                f"Uid={azure_username};"
                f"Pwd=***masked***;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
            result['connection_string_build'] = 'SUCCESS'
            result['connection_string'] = connection_string
        except Exception as e:
            result['connection_string_build'] = 'FAILED'
            result['connection_string_error'] = str(e)
        
        # Test 3: Can we actually connect? (We know this works)
        try:
            conn = pyodbc.connect(
                f"Driver={{ODBC Driver 17 for SQL Server}};"
                f"Server=tcp:{azure_server},1433;"
                f"Database={azure_database};"
                f"Uid={azure_username};"
                f"Pwd={azure_password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
            result['direct_connection'] = 'SUCCESS'
            conn.close()
        except Exception as e:
            result['direct_connection'] = 'FAILED'
            result['connection_error'] = str(e)
            result['error_type'] = type(e).__name__
            
            # If connection fails, it might be due to wrong driver name
            if 'driver' in str(e).lower():
                result['likely_issue'] = 'ODBC Driver not available or wrong name'
    
    except Exception as e:
        result['general_error'] = str(e)
    
    return jsonify(result)

@app.route('/debug/env-detailed')
def debug_env_detailed():
    """Detailed environment variable check for runtime verification"""
    
    # Check each Azure SQL variable individually with actual values (for debugging)
    azure_server = os.environ.get('AZURE_SQL_SERVER')
    azure_database = os.environ.get('AZURE_SQL_DATABASE')
    azure_username = os.environ.get('AZURE_SQL_USERNAME')
    azure_password = os.environ.get('AZURE_SQL_PASSWORD')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'process_id': os.getpid(),
        'runtime_verification': {
            'azure_sql_server': {
                'set': azure_server is not None,
                'length': len(azure_server) if azure_server else 0,
                'preview': azure_server[:20] + '...' if azure_server and len(azure_server) > 20 else azure_server
            },
            'azure_sql_database': {
                'set': azure_database is not None,
                'value': azure_database  # Safe to show database name
            },
            'azure_sql_username': {
                'set': azure_username is not None,
                'value': azure_username  # Safe to show username
            },
            'azure_sql_password': {
                'set': azure_password is not None,
                'length': len(azure_password) if azure_password else 0
            },
            'admin_password': {
                'set': admin_password is not None,
                'length': len(admin_password) if admin_password else 0
            }
        },
        'connection_test': {
            'is_azure_sql_environment': is_azure_sql(),
            'can_build_connection_string': bool(azure_server and azure_database and azure_username and azure_password)
        },
        'system_info': {
            'platform': os.environ.get('WEBSITE_OS_ARCH', 'Unknown'),
            'site_name': os.environ.get('WEBSITE_SITE_NAME', 'Unknown'),
            'python_version': os.environ.get('PYTHON_VERSION', 'Unknown'),
            'total_env_vars': len(os.environ),
            'current_working_dir': os.getcwd(),
            'python_executable': os.environ.get('PYTHON_EXECUTABLE', 'Unknown')
        },
        'process_environment': {
            'environment_type': os.environ.get('ENV', 'development'),
            'flask_env': os.environ.get('FLASK_ENV', 'Not set'),
            'website_hostname': os.environ.get('WEBSITE_HOSTNAME', 'Not set'),
            'runtime_accessible': True  # If this endpoint works, runtime access is confirmed
        }
    })

@app.route('/debug/routes')
def debug_routes():
    """List all registered routes in the Flask application"""
    routes_info = []
    
    for rule in app.url_map.iter_rules():
        route_info = {
            'rule': rule.rule,
            'methods': list(rule.methods),
            'endpoint': rule.endpoint
        }
        routes_info.append(route_info)
    
    # Group routes by category for better organization
    admin_routes = [r for r in routes_info if 'admin' in r['rule']]
    auth_routes = [r for r in routes_info if any(path in r['rule'] for path in ['/login', '/logout', '/register'])]
    user_routes = [r for r in routes_info if any(path in r['rule'] for path in ['/dashboard', '/learnings', '/my-courses', '/profile'])]
    debug_routes = [r for r in routes_info if '/debug' in r['rule']]
    other_routes = [r for r in routes_info if r not in admin_routes + auth_routes + user_routes + debug_routes]
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'total_routes': len(routes_info),
        'categories': {
            'admin_routes': {
                'count': len(admin_routes),
                'routes': admin_routes
            },
            'auth_routes': {
                'count': len(auth_routes),
                'routes': auth_routes
            },
            'user_routes': {
                'count': len(user_routes), 
                'routes': user_routes
            },
            'debug_routes': {
                'count': len(debug_routes),
                'routes': debug_routes
            },
            'other_routes': {
                'count': len(other_routes),
                'routes': other_routes
            }
        }
    })

@app.route('/debug/login-test', methods=['GET', 'POST'])
def debug_login_test():
    """Comprehensive login testing endpoint for Azure debugging"""
    
    if request.method == 'GET':
        # Return a simple form for testing login
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Azure Login Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .form-group { margin: 15px 0; }
                input[type="text"], input[type="password"] { 
                    padding: 8px; margin: 5px; width: 200px; 
                }
                button { padding: 10px 20px; background: #007bff; color: white; border: none; }
                .result { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <h1>Azure Login Test</h1>
            <form method="POST" action="/debug/login-test">
                <div class="form-group">
                    <label>Username:</label><br>
                    <input type="text" name="username" value="admin" required>
                </div>
                <div class="form-group">
                    <label>Password:</label><br>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">Test Login</button>
            </form>
            <p><a href="/debug/routes">View All Routes</a> | <a href="/debug/env">Check Environment</a></p>
        </body>
        </html>
        '''
    
    # POST request - process the login test
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    test_result = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'azure_login_comprehensive',
        'username_provided': username,
        'password_length': len(password) if password else 0,
        'steps': []
    }
    
    try:
        # Step 1: Validate inputs
        step1 = {'step': 1, 'description': 'Input validation'}
        if not username or not password:
            step1['status'] = 'FAIL'
            step1['error'] = 'Username or password missing'
            test_result['steps'].append(step1)
            return jsonify(test_result), 400
        step1['status'] = 'PASS'
        test_result['steps'].append(step1)
        
        # Step 2: Check database connection
        step2 = {'step': 2, 'description': 'Database connection test'}
        try:
            conn = get_db_connection()
            if conn:
                step2['status'] = 'PASS'
                step2['details'] = 'Database connection successful'
            else:
                step2['status'] = 'FAIL'
                step2['error'] = 'Failed to get database connection'
                test_result['steps'].append(step2)
                return jsonify(test_result), 500
        except Exception as e:
            step2['status'] = 'FAIL'
            step2['error'] = f'Database connection error: {str(e)}'
            test_result['steps'].append(step2)
            return jsonify(test_result), 500
        test_result['steps'].append(step2)
        
        # Step 3: Check if user exists
        step3 = {'step': 3, 'description': 'User lookup in database'}
        try:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user:
                step3['status'] = 'PASS'
                step3['details'] = f'User found: {user["username"]}, is_admin: {user["is_admin"]}'
            else:
                step3['status'] = 'FAIL'
                step3['error'] = f'User "{username}" not found in database'
                conn.close()
                test_result['steps'].append(step3)
                return jsonify(test_result), 404
        except Exception as e:
            step3['status'] = 'FAIL'
            step3['error'] = f'User lookup error: {str(e)}'
            conn.close()
            test_result['steps'].append(step3)
            return jsonify(test_result), 500
        test_result['steps'].append(step3)
        
        # Step 4: Password verification
        step4 = {'step': 4, 'description': 'Password verification'}
        try:
            from werkzeug.security import check_password_hash
            if check_password_hash(user['password_hash'], password):
                step4['status'] = 'PASS'
                step4['details'] = 'Password verification successful'
            else:
                step4['status'] = 'FAIL'
                step4['error'] = 'Password verification failed'
                conn.close()
                test_result['steps'].append(step4)
                return jsonify(test_result), 401
        except Exception as e:
            step4['status'] = 'FAIL'
            step4['error'] = f'Password verification error: {str(e)}'
            conn.close()
            test_result['steps'].append(step4)
            return jsonify(test_result), 500
        test_result['steps'].append(step4)
        
        # Step 5: Session creation
        step5 = {'step': 5, 'description': 'Session creation'}
        try:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            step5['status'] = 'PASS'
            step5['details'] = 'Session created successfully'
        except Exception as e:
            step5['status'] = 'FAIL'
            step5['error'] = f'Session creation error: {str(e)}'
            conn.close()
            test_result['steps'].append(step5)
            return jsonify(test_result), 500
        test_result['steps'].append(step5)
        
        # Step 6: Route determination
        step6 = {'step': 6, 'description': 'Route determination'}
        try:
            # Admin status is determined by username, not by is_admin column
            if user['username'] == 'admin':
                redirect_route = 'admin_dashboard'
                step6['details'] = 'Admin user - should redirect to admin dashboard'
                is_admin = True
            else:
                redirect_route = 'dashboard'
                step6['details'] = 'Regular user - should redirect to user dashboard'
                is_admin = False
            step6['status'] = 'PASS'
            step6['redirect_route'] = redirect_route
        except Exception as e:
            step6['status'] = 'FAIL'
            step6['error'] = f'Route determination error: {str(e)}'
            conn.close()
            test_result['steps'].append(step6)
            return jsonify(test_result), 500
        test_result['steps'].append(step6)
        
        conn.close()
        
        # Final result
        test_result['overall_status'] = 'SUCCESS'
        test_result['message'] = 'Login test completed successfully'
        test_result['next_step'] = f'User should be redirected to {redirect_route}'
        test_result['user_details'] = {
            'username': user['username'],
            'is_admin': is_admin,
            'user_id': user['id']
        }
        
        return jsonify(test_result), 200
        
    except Exception as e:
        test_result['overall_status'] = 'ERROR'
        test_result['unexpected_error'] = str(e)
        test_result['error_type'] = type(e).__name__
        return jsonify(test_result), 500

# Note: Removed debug endpoint that exposed admin password for security

@app.route('/debug/reset-admin-password', methods=['POST'])
def debug_reset_admin_password():
    """Securely reset admin password without exposing it in logs"""
    
    try:
        # Get the password from the request (not from environment)
        password = request.form.get('password')
        
        if not password:
            return jsonify({
                'error': 'Password not provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Hash the new password
        password_hash = generate_password_hash(password)
        
        # Update the admin user password in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update admin user password
        if is_azure_sql():
            update_query = "UPDATE users SET password_hash = ? WHERE username = ?"
        else:
            update_query = "UPDATE users SET password_hash = ? WHERE username = ?"
            
        cursor.execute(update_query, (password_hash, 'admin'))
        conn.commit()
        
        # Verify the update
        verify_query = "SELECT username FROM users WHERE username = ?"
        cursor.execute(verify_query, ('admin',))
        admin_user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if admin_user:
            return jsonify({
                'message': 'Admin password reset successfully',
                'status': 'SUCCESS',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'error': 'Admin user not found',
                'status': 'FAIL',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': 'Password reset failed',
            'status': 'ERROR',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/debug/fix-admin-column')
def debug_fix_admin_column():
    """Add is_admin column to Azure SQL database and set admin user to admin"""
    
    results = []
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'error': 'Could not get database connection',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Step 1: Check if is_admin column exists
        try:
            if is_azure_sql():
                # Check for Azure SQL
                check_column = conn.execute("""
                    SELECT COUNT(*) as column_exists 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
                """).fetchone()
                
                column_exists = check_column['column_exists'] > 0
            else:
                # For SQLite, check differently
                try:
                    conn.execute("SELECT is_admin FROM users LIMIT 1")
                    column_exists = True
                except:
                    column_exists = False
            
            results.append(f"✅ Column check: is_admin exists = {column_exists}")
            
        except Exception as e:
            results.append(f"❌ Column check error: {str(e)}")
            column_exists = False
        
        # Step 2: Add is_admin column if it doesn't exist
        if not column_exists:
            try:
                if is_azure_sql():
                    conn.execute("ALTER TABLE users ADD is_admin BIT DEFAULT 0")
                else:
                    conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
                conn.commit()
                results.append("✅ Added is_admin column successfully")
            except Exception as e:
                results.append(f"❌ Error adding is_admin column: {str(e)}")
                conn.close()
                return jsonify({
                    'status': 'FAIL',
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                }), 500
        else:
            results.append("ℹ️  is_admin column already exists")
        
        # Step 3: Update admin user to have is_admin = 1
        try:
            admin_user = conn.execute("SELECT * FROM users WHERE username = ?", ('admin',)).fetchone()
            
            if admin_user:
                if is_azure_sql():
                    conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('admin',))
                else:
                    conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('admin',))
                conn.commit()
                results.append("✅ Updated admin user: set is_admin = 1")
                
                # Verify the update
                updated_admin = conn.execute("SELECT username, is_admin FROM users WHERE username = ?", ('admin',)).fetchone()
                results.append(f"✅ Verification: admin user is_admin = {updated_admin['is_admin']}")
                
            else:
                results.append("❌ Admin user not found in database")
                
        except Exception as e:
            results.append(f"❌ Error updating admin user: {str(e)}")
            conn.close()
            return jsonify({
                'status': 'FAIL',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Step 4: Show all users and their admin status
        try:
            all_users = conn.execute("SELECT username, is_admin FROM users").fetchall()
            user_list = []
            for user in all_users:
                user_list.append({
                    'username': user['username'],
                    'is_admin': bool(user['is_admin'])
                })
            results.append(f"✅ All users: {user_list}")
            
        except Exception as e:
            results.append(f"❌ Error listing users: {str(e)}")
        
        conn.close()
        
        return jsonify({
            'status': 'SUCCESS',
            'message': 'is_admin column fix completed successfully',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'error': str(e),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
