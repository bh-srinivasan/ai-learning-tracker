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
from collections import defaultdict
import re
import requests
from urllib.parse import urlparse

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

# Database configuration
DATABASE = 'ai_learning.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def validate_course_url(url):
    """
    Validate if a course URL is accessible and not retired.
    Returns: ('valid', 'broken', 'retired', 'timeout', 'invalid')
    """
    if not url or url == '#':
        return 'invalid'
    
    try:
        # Parse URL to ensure it's valid
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return 'invalid'
        
        # Set appropriate headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Check for retired or unavailable content indicators
        retired_indicators = [
            'no longer available',
            'content has been retired',
            'course retired',
            'this page is no longer active',
            '404',
            'not found',
            'page not found'
        ]
        
        response_text = response.text.lower()
        
        # Check if page indicates retirement
        for indicator in retired_indicators:
            if indicator in response_text:
                return 'retired'
        
        # Check status codes
        if response.status_code == 200:
            return 'valid'
        elif response.status_code == 404:
            return 'broken'
        elif response.status_code >= 400:
            return 'broken'
        else:
            return 'valid'  # Assume valid for other 2xx or 3xx codes
            
    except requests.exceptions.Timeout:
        return 'timeout'
    except requests.exceptions.RequestException:
        return 'broken'
    except Exception:
        return 'invalid'

def update_course_url_status(course_id, status):
    """Update the URL status for a specific course"""
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE courses 
            SET url_status = ?, last_url_check = datetime('now'),
                is_active = CASE WHEN ? IN ('retired', 'broken') THEN 0 ELSE 1 END,
                is_retired = CASE WHEN ? = 'retired' THEN 1 ELSE 0 END
            WHERE id = ?
        ''', (status, status, status, course_id))
        conn.commit()
    finally:
        conn.close()

def check_and_update_all_course_urls():
    """Background function to check all course URLs (should be run periodically)"""
    conn = get_db_connection()
    try:
        courses = conn.execute('SELECT id, url, link FROM courses WHERE is_active = 1').fetchall()
        updated_count = 0
        
        for course in courses:
            course_id = course['id']
            url = course['url'] or course['link']
            
            if url:
                status = validate_course_url(url)
                update_course_url_status(course_id, status)
                updated_count += 1
                
                # Add small delay to avoid overwhelming servers
                time.sleep(0.5)
        
        return updated_count
    finally:
        conn.close()

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
    
    # Update existing courses table to add new columns
    try:
        conn.execute('ALTER TABLE courses ADD COLUMN is_active BOOLEAN DEFAULT 1')
        conn.execute('ALTER TABLE courses ADD COLUMN is_retired BOOLEAN DEFAULT 0')
        conn.execute('ALTER TABLE courses ADD COLUMN url_status TEXT DEFAULT "unchecked"')
        conn.execute('ALTER TABLE courses ADD COLUMN last_url_check TIMESTAMP')
        conn.commit()
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Create default users (only admin and demo for testing)
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
    demo_password = os.environ.get('DEMO_PASSWORD', 'demo')
    
    admin_hash = generate_password_hash(admin_password)
    demo_hash = generate_password_hash(demo_password)
    
    try:
        # Create admin user
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
        # Create demo user for testing
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('demo', demo_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        # Users already exist
        pass
    
    conn.close()

# Helper functions
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

# Dashboard route
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

# My Courses route
@app.route('/dashboard/my-courses')
@require_auth
def dashboard_my_courses():
    """Display user's courses"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get filter parameters
    search_query = request.args.get('search', '')
    date_filter = request.args.get('date_filter', '')
        
    conn = get_db_connection()
    try:
        # Base query for completed courses
        completed_query = '''
            SELECT c.*, uc.completed, uc.completion_date, 'system' as course_type
            FROM courses c 
            INNER JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ? AND uc.completed = 1
        '''
        completed_params = [user['id']]
        
        # Apply search filter to completed courses
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
        
        # Base query for recommended courses - only show active courses with valid URLs
        recommended_query = '''
            SELECT c.*, COALESCE(uc.completed, 0) as completed, 'recommended' as course_type
            FROM courses c 
            LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
            WHERE (uc.completed IS NULL OR uc.completed = 0)
            AND c.is_active = 1 
            AND c.is_retired = 0 
            AND c.url_status NOT IN ('broken', 'retired')
            AND (c.url IS NOT NULL AND c.url != '' AND c.url != '#')
        '''
        recommended_params = [user['id']]
        
        # Apply search filter to recommended courses
        if search_query:
            recommended_query += ' AND (c.title LIKE ? OR c.description LIKE ?)'
            recommended_params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        recommended_query += ' ORDER BY c.created_at DESC'
        recommended_courses = conn.execute(recommended_query, recommended_params).fetchall()
        
        return render_template('dashboard/my_courses.html', 
                             completed_courses=completed_courses,
                             recommended_courses=recommended_courses,
                             current_filters={
                                 'date_filter': date_filter,
                                 'search': search_query
                             })
    finally:
        conn.close()

# Admin routes
@app.route('/admin')
@require_admin
def admin():
    return render_template('admin/index.html')

@app.route('/admin/courses')
@require_admin
def admin_courses():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/check-course-urls', methods=['POST'])
@require_admin
def admin_check_course_urls():
    """Check and update all course URLs (admin only)"""
    try:
        updated_count = check_and_update_all_course_urls()
        flash(f'Checked and updated {updated_count} course URLs!', 'success')
    except Exception as e:
        flash(f'Error checking course URLs: {str(e)}', 'error')
    
    return redirect(url_for('admin_courses'))

@app.route('/admin/toggle-course-status/<int:course_id>', methods=['POST'])
@require_admin  
def admin_toggle_course_status(course_id):
    """Toggle course active/retired status (admin only)"""
    action = request.form.get('action', 'toggle')
    
    conn = get_db_connection()
    try:
        if action == 'activate':
            conn.execute('''
                UPDATE courses 
                SET is_active = 1, is_retired = 0, url_status = 'unchecked'
                WHERE id = ?
            ''', (course_id,))
            flash('Course activated successfully!', 'success')
        elif action == 'retire':
            conn.execute('''
                UPDATE courses 
                SET is_active = 0, is_retired = 1, url_status = 'retired'
                WHERE id = ?
            ''', (course_id,))
            flash('Course retired successfully!', 'success')
        else:
            # Toggle status
            course = conn.execute('SELECT is_active FROM courses WHERE id = ?', (course_id,)).fetchone()
            if course:
                new_status = 0 if course['is_active'] else 1
                conn.execute('''
                    UPDATE courses 
                    SET is_active = ?, is_retired = ?, url_status = CASE WHEN ? = 0 THEN 'retired' ELSE 'unchecked' END
                    WHERE id = ?
                ''', (new_status, 1 - new_status, new_status, course_id))
                status_text = 'activated' if new_status else 'retired'
                flash(f'Course {status_text} successfully!', 'success')
        
        conn.commit()
    except Exception as e:
        flash(f'Error updating course status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_courses'))

# Complete course route
@app.route('/complete-course/<int:course_id>', methods=['POST'])
@require_auth
def complete_course(course_id):
    """Mark a course as completed"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Check if user is already enrolled
        existing = conn.execute('''
            SELECT * FROM user_courses 
            WHERE user_id = ? AND course_id = ?
        ''', (user['id'], course_id)).fetchone()
        
        if existing:
            # Update to completed
            conn.execute('''
                UPDATE user_courses 
                SET completed = 1, completion_date = datetime('now') 
                WHERE user_id = ? AND course_id = ?
            ''', (user['id'], course_id))
        else:
            # Insert new enrollment as completed
            conn.execute('''
                INSERT INTO user_courses (user_id, course_id, completed, completion_date)
                VALUES (?, ?, 1, datetime('now'))
            ''', (user['id'], course_id))
        
        conn.commit()
        flash('Course marked as completed!', 'success')
    except Exception as e:
        flash(f'Error completing course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard_my_courses'))

# Learning entries routes
@app.route('/learnings')
@require_auth
def learnings():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    entries = conn.execute('''
        SELECT * FROM learning_entries 
        WHERE user_id = ? 
        ORDER BY date_added DESC
    ''', (user['id'],)).fetchall()
    conn.close()
    
    return render_template('learnings/index.html', entries=entries)

@app.route('/learnings/add', methods=['GET', 'POST'])
@require_auth
def add_learning():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        tags = request.form.get('tags', '')
        custom_date = request.form.get('custom_date')
        
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        try:
            if custom_date:
                conn.execute('''
                    INSERT INTO learning_entries (user_id, title, description, tags, custom_date, date_added)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (user['id'], title, description, tags, custom_date))
            else:
                conn.execute('''
                    INSERT INTO learning_entries (user_id, title, description, tags)
                    VALUES (?, ?, ?, ?)
                ''', (user['id'], title, description, tags))
            
            conn.commit()
            flash('Learning entry added successfully!', 'success')
            return redirect(url_for('learnings'))
        except Exception as e:
            flash(f'Error adding learning entry: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('learnings/add.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
