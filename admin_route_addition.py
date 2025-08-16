@app.route('/force-init-admin')
def force_init_admin():
    """Force admin initialization - emergency route"""
    try:
        conn = get_db_connection()
        
        # Create users table if it doesn't exist
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
            return f"<h2>✅ Admin user already exists</h2><p>Admin ID: {existing_admin['id']}</p><a href='/'>Go to Login</a>"
        
        # Create admin user
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 100, 'active', 'Advanced', 0))
        
        conn.commit()
        admin_id = conn.lastrowid
        conn.close()
        
        return f"<h2>✅ Admin user created!</h2><p>ID: {admin_id}</p><p>Username: admin</p><p>Password: YourSecureAdminPassword123!</p><a href='/'>Login Now</a>"
        
    except Exception as e:
        return f"<h2>❌ Error: {str(e)}</h2><p>Check logs for details</p>"
