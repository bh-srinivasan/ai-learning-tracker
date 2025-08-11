import pyodbc
from werkzeug.security import generate_password_hash

# Reset admin password in Azure SQL
server = 'ai-learning-sql-centralus.database.windows.net'
database = 'ai-learning-db'
username = 'ailearningadmin'
password = 'AiAzurepass!2025'

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("=================================")
print("Azure SQL Admin Password Reset")
print("=================================")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Generate new password hash for 'admin'
    new_password = 'admin'
    new_password_hash = generate_password_hash(new_password)
    
    print(f"🔧 Resetting admin password to: {new_password}")
    print(f"   New hash: {new_password_hash[:30]}...")
    
    # Update admin user password
    cursor.execute("""
        UPDATE users 
        SET password_hash = ? 
        WHERE username = 'admin'
    """, (new_password_hash,))
    
    conn.commit()
    print("✅ Admin password updated successfully!")
    
    # Verify the update
    cursor.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        print(f"✅ Verification: Admin user found")
        print(f"   Username: {admin_user[0]}")
        print(f"   New hash: {admin_user[1][:30]}...")
        
        # Test the new password
        from werkzeug.security import check_password_hash
        if check_password_hash(admin_user[1], new_password):
            print(f"✅ Password verification successful!")
        else:
            print(f"❌ Password verification failed!")
    
    cursor.close()
    conn.close()
    print("\n🎉 Admin password reset completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
