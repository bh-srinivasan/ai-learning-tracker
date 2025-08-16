"""
Simple fix to create admin user directly in Azure without complex initialization
"""

# Add this simple route to app.py for direct admin creation
ADMIN_CREATION_ROUTE = """
@app.route('/create-admin-now')
def create_admin_now():
    '''Emergency route to create admin user directly'''
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
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('YourSecureAdminPassword123!')
        
        conn.execute('''
            INSERT INTO users (username, password_hash, level, points, status, user_selected_level, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Advanced', 100, 'active', 'Advanced', 0))
        
        conn.commit()
        admin_id = conn.lastrowid
        conn.close()
        
        return f"<h2>✅ Admin user created successfully!</h2><p>Admin ID: {admin_id}</p><p>Username: admin</p><p>You can now login at <a href='/'>the login page</a></p>"
        
    except Exception as e:
        return f"<h2>❌ Error creating admin: {str(e)}</h2><a href='/create-admin-now'>Try Again</a>"
'''

print("Add this route to your app.py file:")
print(ADMIN_CREATION_ROUTE)
