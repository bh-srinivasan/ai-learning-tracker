#!/usr/bin/env python3
"""
Secure Admin Password Reset for Azure
Takes password from terminal input - no hardcoding
"""

import os
import sys
import getpass
from werkzeug.security import generate_password_hash

def reset_admin_password_azure():
    """Reset admin password in Azure SQL Database"""
    
    print("🔐 Secure Admin Password Reset for Azure")
    print("=" * 50)
    
    # Get password from secure terminal input (won't echo to screen)
    try:
        new_password = getpass.getpass("Enter new admin password: ")
        confirm_password = getpass.getpass("Confirm admin password: ")
        
        if new_password != confirm_password:
            print("❌ Passwords don't match. Aborting.")
            return False
            
        if len(new_password) < 8:
            print("❌ Password must be at least 8 characters. Aborting.")
            return False
            
    except KeyboardInterrupt:
        print("\n❌ Password reset cancelled.")
        return False
    
    # Generate secure hash
    try:
        password_hash = generate_password_hash(new_password)
        print("✅ Password hash generated successfully")
    except Exception as e:
        print(f"❌ Error generating password hash: {e}")
        return False
    
    # Connect to Azure SQL Database
    try:
        import pyodbc
        
        # Azure SQL connection details (hardcoded for this specific case)
        server = 'ai-learning-sql-centralus.database.windows.net'
        database = 'ai-learning-db'
        username = 'ailearningadmin'
        password = 'AiAzurepass!2025'
        
        # Build connection string
        connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        
        print("🔄 Connecting to Azure SQL Database...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Update admin password
        print("🔄 Updating admin password...")
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (password_hash,)
        )
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"✅ Admin password updated successfully! ({rows_affected} row(s) affected)")
            
            # Verify the update worked
            from werkzeug.security import check_password_hash
            cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
            result = cursor.fetchone()
            
            if result and check_password_hash(result[0], new_password):
                print("✅ Password verification successful!")
                print("🎉 Admin password reset completed!")
                return True
            else:
                print("❌ Password verification failed!")
                return False
        else:
            print("❌ No admin user found to update")
            return False
            
    except ImportError:
        print("❌ pyodbc not available. Cannot connect to Azure SQL.")
        return False
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
    
    # Clear password variables from memory
    new_password = None
    confirm_password = None
    password_hash = None

if __name__ == "__main__":
    success = reset_admin_password_azure()
    sys.exit(0 if success else 1)
