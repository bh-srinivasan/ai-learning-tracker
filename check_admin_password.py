import pyodbc
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Check admin user password in Azure SQL
server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
username = os.environ.get('AZURE_SQL_USERNAME', 'ailearningadmin')
password = os.environ.get('AZURE_SQL_PASSWORD')

# Validate required environment variables
if not password:
    print("❌ ERROR: AZURE_SQL_PASSWORD environment variable is required!")
    print("Please set it in your .env file or environment variables.")
    sys.exit(1)

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("=================================")
print("Azure SQL Admin User Check")
print("=================================")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Get admin user details
    print("📋 Admin user details:")
    cursor.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = 'admin'")
    
    admin_user = cursor.fetchone()
    if admin_user:
        user_id, username, password_hash, is_admin = admin_user
        print(f"   ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Password Hash: {password_hash[:20]}...")
        print(f"   Is Admin: {is_admin}")
        
        # Test password verification
        from werkzeug.security import check_password_hash
        
        test_passwords = ['admin', 'Admin123!', 'password', 'admin123']
        
        print(f"\n🔧 Testing passwords...")
        for test_pass in test_passwords:
            if check_password_hash(password_hash, test_pass):
                print(f"   ✅ Password '{test_pass}' matches!")
                break
        else:
            print("   ❌ None of the test passwords match")
            print("   📝 Password hash needs to be reset")
            
    else:
        print("❌ Admin user not found!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
