#!/usr/bin/env python3
"""
Azure Admin Fix using existing app infrastructure
"""

import sys
import os

# Add the current directory to Python path to import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_azure_admin():
    """Fix Azure admin using existing app functions"""
    
    print("=" * 60)
    print("AZURE ADMIN FIX VIA APP INFRASTRUCTURE")
    print("=" * 60)
    
    try:
        # Import app functions
        from app import get_db_connection, is_azure_sql
        
        print("🔗 Checking Azure SQL connection...")
        
        if not is_azure_sql():
            print("❌ Not configured for Azure SQL - missing environment variables")
            return False
            
        print("✅ Azure SQL configuration detected")
        
        conn = get_db_connection()
        if not conn:
            print("❌ Could not connect to Azure SQL database")
            return False
            
        print("✅ Connected to Azure SQL database")
        
        # Step 1: Check if is_admin column exists and add if needed
        print("\n1. Checking/Adding is_admin column...")
        try:
            # Try to query is_admin column
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 is_admin FROM users WHERE username = ?", ('admin',))
            result = cursor.fetchone()
            print("   ✅ is_admin column exists")
            
        except Exception as e:
            if "Invalid column name 'is_admin'" in str(e):
                print("   ❌ is_admin column missing - adding it...")
                try:
                    cursor.execute("ALTER TABLE users ADD is_admin BIT DEFAULT 0")
                    conn.commit()
                    print("   ✅ is_admin column added")
                except Exception as add_error:
                    print(f"   ❌ Error adding column: {add_error}")
                    return False
            else:
                print(f"   ❌ Unexpected error: {e}")
                return False
        
        # Step 2: Set admin user privileges
        print("\n2. Setting admin privileges...")
        try:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('admin',))
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected > 0:
                print(f"   ✅ Updated admin user (rows affected: {rows_affected})")
            else:
                print("   ⚠️  No rows updated - admin user may not exist")
        
        except Exception as e:
            print(f"   ❌ Error setting admin privileges: {e}")
            return False
        
        # Step 3: Verify the fix
        print("\n3. Verifying admin user...")
        try:
            cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", ('admin',))
            admin_user = cursor.fetchone()
            
            if admin_user:
                is_admin_value = admin_user[2] if len(admin_user) > 2 else None
                print(f"   ✅ Admin user found:")
                print(f"      ID: {admin_user[0]}")
                print(f"      Username: {admin_user[1]}")
                print(f"      Is Admin: {is_admin_value}")
                
                if is_admin_value:
                    print("   ✅ Admin privileges verified!")
                    return True
                else:
                    print("   ❌ Admin privileges not set correctly")
                    return False
            else:
                print("   ❌ Admin user not found")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verifying admin: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import app functions: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        try:
            conn.close()
            print("\n🔗 Database connection closed")
        except:
            pass
    
    print("=" * 60)

if __name__ == "__main__":
    success = fix_azure_admin()
    if success:
        print("🎉 Azure admin fix completed successfully!")
        print("Now the Azure app should work with admin login.")
    else:
        print("❌ Azure admin fix failed!")
        print("Manual intervention may be required.")
