#!/usr/bin/env python3
"""
One-Line Admin Creator
======================

Simple one-line command to create admin user in Azure console.
Copy and paste this command in Azure Kudu console.
"""

# ONE-LINE COMMAND FOR AZURE CONSOLE:
# python -c "import sqlite3,hashlib,secrets; conn=sqlite3.connect('ai_learning.db'); c=conn.cursor(); c.execute('SELECT id FROM users WHERE username=\"admin\"') and print('Admin exists') or [c.execute('INSERT INTO users (username,password_hash,level,points,status,user_selected_level,login_count,created_at) VALUES (?,?,?,?,?,?,?,?)', ('admin', f'pbkdf2:sha256:100000${secrets.token_hex(16)}${hashlib.pbkdf2_hmac(\"sha256\", \"YourSecureAdminPassword123!\".encode(), secrets.token_hex(16).encode(), 100000).hex()}', 'Advanced', 1000, 'active', 'Advanced', 0, '2025-07-19T00:00:00')), conn.commit(), print('Admin created!')]; conn.close()"

print("""
AZURE CONSOLE COMMAND:
======================

Copy and paste this ONE LINE in Azure Kudu Console:

python -c "import sqlite3,hashlib,secrets,os; pw=os.environ.get('ADMIN_PASSWORD','YourSecureAdminPassword123!'); conn=sqlite3.connect('ai_learning.db'); c=conn.cursor(); existing=c.execute('SELECT id FROM users WHERE username=\"admin\"').fetchone(); print('✅ Admin already exists') if existing else [c.execute('INSERT INTO users (username,password_hash,level,points,status,user_selected_level,login_count,created_at) VALUES (?,?,?,?,?,?,?,?)', ('admin', f'pbkdf2:sha256:100000$salt${hashlib.pbkdf2_hmac(\"sha256\", pw.encode(), b\"salt\", 100000).hex()}', 'Advanced', 1000, 'active', 'Advanced', 0, '2025-07-19')), conn.commit(), print(f'🎉 Admin created! Username: admin, Password: {pw}')]; conn.close()"

STEPS:
1. Go to Azure Portal → ai-learning-tracker-bharath → Advanced Tools → Go
2. Click "Debug console" → "CMD"  
3. Navigate: Click 'site' → 'wwwroot'
4. Paste the command above and press Enter

RESULT: Admin user will be created with secure password hashing!
""")

if __name__ == "__main__":
    print(__doc__)
