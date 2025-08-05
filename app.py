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
    
    # Wrap execute to return rows with dict-like access
    original_execute = conn.execute
    def enhanced_execute(query, params=()):
        cursor = conn.cursor()
        
        # Basic query conversions for common SQLite -> SQL Server differences
        if 'AUTOINCREMENT' in query.upper():
            query = query.replace('AUTOINCREMENT', 'IDENTITY(1,1)')
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'INT IDENTITY(1,1) PRIMARY KEY')
        
        cursor.execute(query, params)
        
        # Wrap fetchone and fetchall
        original_fetchone = cursor.fetchone
        original_fetchall = cursor.fetchall
        
        def fetchone():
            row = original_fetchone()
            return SimpleRow(cursor, row) if row else None
            
        def fetchall():
            rows = original_fetchall()
            return [SimpleRow(cursor, row) for row in rows] if rows else []
        
        cursor.fetchone = fetchone
        cursor.fetchall = fetchall
        return cursor
    
    # Add cursor method for direct Azure SQL operations
    def get_cursor():
        return conn.cursor()
    
    conn.execute = enhanced_execute
    conn.cursor = get_cursor
    logger.info("Azure SQL Database connection established with SQLite compatibility wrapper")
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
        # Invalidate old sessions for this user
        if is_azure_sql():
            # Azure SQL Database session creation
            conn.execute(f'''
                UPDATE {session_table} 
                SET is_active = 0 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            # Create new session with all required columns
            conn.execute(f'''
                INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at, last_activity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_token, user_id, ip_address, user_agent, expires_at, datetime.now()))
        else:
            # SQLite Database session creation
            conn.execute(f'''
                UPDATE {session_table} 
                SET is_active = 0 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            # Create new session
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

@app.route('/debug-session')
def debug_session():
    """Debug endpoint to check session state"""
    try:
        session_token = session.get('session_token')
        debug_info = {
            'session_token': session_token,
            'azure_sql_env': os.getenv('AZURE_SQL_CONNECTION_STRING'),
            'sqlserver_env': os.getenv('SQLAZURECONNSTR_DEFAULTCONNECTION'),
            'all_env_vars': [k for k in os.environ.keys() if 'SQL' in k.upper() or 'CONNECTION' in k.upper()],
            'has_azure_sql': bool(os.getenv('AZURE_SQL_CONNECTION_STRING')),
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

@app.route('/test-azure-connection')
def test_azure_connection():
    """Test Azure SQL connection directly to diagnose issues"""
    try:
        import pyodbc
        
        # Test direct connection to Azure SQL
        print("🔄 Testing direct Azure SQL connection...")
        print(f"Connection string: {AZURE_CONNECTION_STRING[:50]}...")
        
        # Try direct pyodbc connection
        conn = pyodbc.connect(AZURE_CONNECTION_STRING)
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
            'message': 'Direct Azure SQL connection successful'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Direct Azure SQL connection failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__,
            'connection_string_present': bool(AZURE_CONNECTION_STRING)
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
            'next_step': 'Update AZURE_SQL_CONNECTION_STRING environment variable in Azure App Service'
        })
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Table creation failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__
        })

@app.route('/create-tables-azure')
def create_tables_azure():
    """Create missing tables in Azure SQL using direct connection"""
    try:
        import pyodbc
        
        # Use direct connection to avoid wrapper fallback
        conn = pyodbc.connect(AZURE_CONNECTION_STRING)
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
            'connection_method': 'direct_pyodbc'
        })
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Table creation failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__,
            'connection_string_present': bool(AZURE_CONNECTION_STRING)
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
        test_password = 'AILearning2025!'
        
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
                admin_password = "AILearning2025!"
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
