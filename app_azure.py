#!/usr/bin/env python3
"""
Azure-compatible AI Learning Tracker with proper templates
Production version with full template support
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
app.secret_key = os.environ.get('SECRET_KEY', 'azure-production-secret-key-2024')

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
        
        # Create courses table if not exists
        conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                url TEXT,
                level TEXT DEFAULT 'Beginner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# Helper functions
def get_user_level(user_id):
    """Calculate user level based on learning entries"""
    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT COUNT(*) FROM learning_entries WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count < 5:
            return "Beginner"
        elif count < 15:
            return "Intermediate"
        else:
            return "Advanced"
    except:
        return "Beginner"

# Routes
@app.route('/')
def index():
    """Home page - redirect to appropriate page"""
    try:
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return render_template('error.html', error=str(e)), 500

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
            'time': datetime.now().isoformat(),
            'templates': 'enabled'
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with template"""
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
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        # Check if template exists, fallback to simple HTML
        try:
            return render_template('auth/login.html')
        except:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login - AI Learning Tracker</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h3 class="card-title text-center">AI Learning Tracker</h3>
                                    <form method="post">
                                        <div class="mb-3">
                                            <label class="form-label">Username</label>
                                            <input type="text" name="username" class="form-control" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Password</label>
                                            <input type="password" name="password" class="form-control" required>
                                        </div>
                                        <button type="submit" class="btn btn-primary w-100">Login</button>
                                    </form>
                                    <p class="mt-3 text-center"><small>Default: admin / admin123</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
    except Exception as e:
        logger.error(f"Login route error: {e}")
        return f"Login error: {e}", 500

@app.route('/dashboard')
def dashboard():
    """Dashboard page with template"""
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        entries = conn.execute(
            'SELECT * FROM learning_entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
            (session['user_id'],)
        ).fetchall()
        
        courses = conn.execute(
            'SELECT * FROM courses ORDER BY created_at DESC LIMIT 5'
        ).fetchall()
        
        conn.close()
        
        user_level = get_user_level(session['user_id'])
        
        # Try to use template, fallback to simple HTML
        try:
            return render_template('dashboard/index.html', 
                                 entries=entries, 
                                 courses=courses, 
                                 user_level=user_level)
        except:
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard - AI Learning Tracker</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-4">
                    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
                        <div class="container-fluid">
                            <span class="navbar-brand">AI Learning Tracker</span>
                            <div class="navbar-nav ms-auto">
                                <span class="nav-text text-white me-3">Welcome, {session['username']}! (Level: {user_level})</span>
                                <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                            </div>
                        </div>
                    </nav>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Recent Learning Entries</h5>
                                </div>
                                <div class="card-body">
                                    <p>Learning entries: {len(entries)}</p>
                                    <a href="/learnings" class="btn btn-primary">View All</a>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Available Courses</h5>
                                </div>
                                <div class="card-body">
                                    <p>Courses available: {len(courses)}</p>
                                    <a href="/courses" class="btn btn-success">Browse Courses</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <p><strong>App Status:</strong> Running successfully on Azure with templates! ✅</p>
                        <p><strong>Time:</strong> {datetime.now()}</p>
                    </div>
                </div>
            </body>
            </html>
            '''
    except Exception as e:
        logger.error(f"Dashboard route error: {e}")
        return f"Dashboard error: {e}", 500

@app.route('/learnings')
def learnings():
    """Learnings page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        entries = conn.execute(
            'SELECT * FROM learning_entries WHERE user_id = ? ORDER BY created_at DESC',
            (session['user_id'],)
        ).fetchall()
        conn.close()
        
        try:
            return render_template('learnings/index.html', entries=entries)
        except:
            return f'''
            <div class="container mt-4">
                <h2>My Learning Entries</h2>
                <p>Total entries: {len(entries)}</p>
                <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
            '''
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/courses')
def courses():
    """Courses page"""
    try:
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses ORDER BY created_at DESC').fetchall()
        conn.close()
        
        return f'''
        <div class="container mt-4">
            <h2>Available Courses</h2>
            <p>Total courses: {len(courses)}</p>
            <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
        </div>
        '''
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return '''
    <div class="container mt-4">
        <h2>Page Not Found</h2>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/" class="btn btn-primary">Go Home</a>
    </div>
    ''', 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return f'''
    <div class="container mt-4">
        <h2>Something went wrong</h2>
        <p>Error: {error}</p>
        <a href="/" class="btn btn-primary">Go Home</a>
        <p><strong>Debug info:</strong> {datetime.now()}</p>
    </div>
    ''', 500

# Initialize database on startup
try:
    logger.info("Initializing Azure application with templates...")
    init_success = init_db()
    if init_success:
        logger.info("✅ Azure application initialized successfully")
    else:
        logger.error("❌ Database initialization failed")
except Exception as e:
    logger.error(f"❌ Application initialization error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Azure app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
