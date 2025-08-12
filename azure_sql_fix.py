import pyodbc
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure SQL Database connection details from environment variables
server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
username = os.environ.get('AZURE_SQL_USERNAME', 'ailearningadmin')
password = os.environ.get('AZURE_SQL_PASSWORD')

# Validate required environment variables
if not password:
    print("❌ ERROR: AZURE_SQL_PASSWORD environment variable is required!")
    print("Please set it in your .env file or environment variables.")
    print("Example: AZURE_SQL_PASSWORD=your_secure_password")
    sys.exit(1)

# Connection string
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("=================================")
print("Azure SQL Database Schema Fix")
print("=================================")
print(f"Server: {server}")
print(f"Database: {database}")
print(f"Username: {username}")
print("Password: [PROTECTED]")
print()

try:
    # Connect to the database
    print("🔗 Connecting to Azure SQL Database...")
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ Connected successfully!")
    
    # Check if is_admin column exists
    print("\n🔍 Checking if is_admin column exists...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
    """)
    column_exists = cursor.fetchone()[0]
    
    if column_exists > 0:
        print("✅ is_admin column already exists!")
    else:
        print("❌ is_admin column not found. Adding it...")
        
        # Add the is_admin column
        cursor.execute("ALTER TABLE users ADD is_admin BIT DEFAULT 0")
        print("✅ Added is_admin column")
        
        # Set admin user as admin
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
        affected_rows = cursor.rowcount
        print(f"✅ Updated admin user (affected rows: {affected_rows})")
        
        # Commit changes
        conn.commit()
        print("✅ Changes committed to database")
    
    # Verify the fix
    print("\n🔍 Verifying admin user...")
    cursor.execute("SELECT username, is_admin FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        username, is_admin = admin_user
        print(f"✅ Admin user found: {username}, is_admin: {is_admin}")
    else:
        print("❌ Admin user not found!")
    
    cursor.close()
    conn.close()
    print("\n🎉 Azure SQL Database fix completed successfully!")
    print("✅ Admin user should now have proper permissions")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
