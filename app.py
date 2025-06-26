from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ai-learning-tracker-secret-key'

# Database configuration
DATABASE = 'ai_learning.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    
    # Users table - add status and user_selected_level fields
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            level TEXT DEFAULT 'Beginner',
            points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            user_selected_level TEXT DEFAULT 'Beginner',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    # Courses table - add points field
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            level TEXT NOT NULL,
            link TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # Update existing users table to add points column if it doesn't exist
    try:
        conn.execute('ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0')
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

# Initialize database on startup
init_db()

# Import blueprints
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from learnings.routes import learnings_bp
from admin.routes import admin_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(learnings_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)
