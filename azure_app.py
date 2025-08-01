from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'azure-production-secret-key-2024')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables and admin user"""
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create learnings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            date_learned DATE NOT NULL,
            category TEXT,
            level TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user
    admin_password = os.getenv('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
    admin_hash = generate_password_hash(admin_password)
    
    try:
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                    ('admin', admin_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Admin user already exists
    
    conn.close()

@app.route('/')
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        # Calculate user level
        conn = get_db_connection()
        learning_count = conn.execute('SELECT COUNT(*) FROM learnings WHERE user_id = ?', 
                                    (user['id'],)).fetchone()[0]
        conn.close()
        
        if learning_count >= 50:
            session['user_level'] = 'Expert'
        elif learning_count >= 20:
            session['user_level'] = 'Advanced'
        elif learning_count >= 10:
            session['user_level'] = 'Intermediate'
        else:
            session['user_level'] = 'Beginner'
        
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['username'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    learnings = conn.execute('''
        SELECT * FROM learnings WHERE user_id = ? 
        ORDER BY date_learned DESC LIMIT 5
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', learnings=learnings)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get user statistics
    users = conn.execute('SELECT * FROM users').fetchall()
    total_learnings = conn.execute('SELECT COUNT(*) FROM learnings').fetchone()[0]
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         users=users, 
                         total_learnings=total_learnings)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
