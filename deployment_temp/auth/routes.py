from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import check_password_hash
import sqlite3

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Check if IP is blocked
    client_ip = request.remote_addr
    from app import is_ip_blocked, check_rate_limit
    
    if is_ip_blocked(client_ip):
        flash('Access temporarily blocked due to too many failed login attempts. Please try again later.', 'error')
        return render_template('auth/login.html', blocked=True)
    
    # If user is already logged in, redirect to dashboard
    session_token = session.get('session_token')
    if session_token:
        # Import session validation function from app
        from app import validate_session
        if validate_session(session_token, request):
            return redirect(url_for('dashboard.index'))
        else:
            # Clear invalid session
            session.clear()
    
    if request.method == 'POST':
        # Check rate limiting before processing
        if not check_rate_limit(client_ip, 'login'):
            flash('Too many login attempts. Access temporarily blocked.', 'error')
            return render_template('auth/login.html', blocked=True)
        
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me') == 'on'
        
        # Basic input sanitization while keeping login simple
        from app import sanitize_input
        username = sanitize_input(username)
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # Check if user is active
            if user['status'] == 'inactive':
                flash('Your account has been paused. Please contact the administrator.', 'error')
                from app import log_security_event
                log_security_event('inactive_account_access', f'Inactive account access attempt: {username}', client_ip)
                return render_template('auth/login.html')
            
            # Detect suspicious activity
            from app import detect_suspicious_activity
            if detect_suspicious_activity(user['id'], client_ip, request.headers.get('User-Agent')):
                flash('Unusual activity detected. Please contact administrator if this wasn\'t you.', 'warning')
            
            # Create new session using session management
            from app import create_user_session, log_security_event
            session_token = create_user_session(
                user['id'], 
                client_ip, 
                request.headers.get('User-Agent')
            )
            
            # Set session data
            session['session_token'] = session_token
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_level'] = user['level']
            
            # Make session permanent if remember me is checked
            if remember_me:
                session.permanent = True
            
            # Clear failed attempts for this IP on successful login
            from app import login_attempts, failed_attempts
            if client_ip in login_attempts:
                del login_attempts[client_ip]
            if client_ip in failed_attempts:
                del failed_attempts[client_ip]
            
            # Log successful login
            log_security_event('successful_login', f'User {username} logged in successfully', client_ip, user['id'])
            
            flash('Successfully logged in!', 'success')
            
            # Redirect to next page if specified
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            # Record failed attempt
            from app import record_failed_attempt
            record_failed_attempt(client_ip, username)
            flash('Invalid username or password', 'error')
    
    # Check if should show captcha (for future enhancement)
    show_captcha = False
    if client_ip in failed_attempts:
        from app import SECURITY_CONFIG
        show_captcha = failed_attempts[client_ip] >= SECURITY_CONFIG['ENABLE_CAPTCHA_AFTER_ATTEMPTS']
    
    return render_template('auth/login.html', show_captcha=show_captcha)

@auth_bp.route('/logout')
def logout():
    # Invalidate session using session management
    session_token = session.get('session_token')
    if session_token:
        from app import invalidate_session
        invalidate_session(session_token)
    
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
