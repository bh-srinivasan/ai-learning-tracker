#!/usr/bin/env python3
"""
Azure Database Connection Test
Verify Azure database connectivity and basic structure
"""

from database_manager import get_db_connection
import os

def test_azure_connection():
    """Test Azure database connection and basic queries"""
    print("🔍 AZURE DATABASE CONNECTION TEST")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Check:")
    db_path = os.environ.get('DATABASE_URL', 'Not set')
    print(f"   DATABASE_URL: {db_path}")
    
    try:
        # Test connection
        print("\n🔗 Testing Azure database connection...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"✅ Connection successful - {table_count} tables found")
        
        # Check if this is actually Azure or local
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table = cursor.fetchone()
        
        if users_table:
            # Check admin user to verify environment
            cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
            admin_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            print(f"👥 Users table: {total_users} total users, Admin exists: {'Yes' if admin_count > 0 else 'No'}")
            
            # Check recent activity to verify this is Azure
            cursor.execute("SELECT MAX(last_login) FROM users WHERE username='admin'")
            last_admin_login = cursor.fetchone()[0]
            print(f"🔐 Admin last login: {last_admin_login or 'Never'}")
            
        else:
            print("❌ Users table not found!")
        
        # Check database file location
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchall()
        print(f"\n📁 Database file location:")
        for db in db_info:
            print(f"   {db[1]}: {db[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Azure database connection failed: {e}")
        return False

def verify_azure_vs_local():
    """Verify we're actually connecting to Azure, not local"""
    print("\n🔍 VERIFYING AZURE CONNECTION (NOT LOCAL)")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check database file path
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchall()
        
        for db in db_info:
            db_file = db[2]
            print(f"📁 Connected to: {db_file}")
            
            # Determine if this looks like Azure or local
            if 'ai_learning.db' in str(db_file).lower():
                print("⚠️  WARNING: This appears to be LOCAL database!")
                print("⚠️  File name suggests local SQLite file")
            elif 'azure' in str(db_file).lower() or 'temp' in str(db_file).lower():
                print("✅ This appears to be Azure database")
            else:
                print(f"❓ Unknown database type: {db_file}")
        
        # Check user data characteristics
        cursor.execute("SELECT username, created_at, last_login FROM users ORDER BY id LIMIT 5")
        users = cursor.fetchall()
        
        print(f"\n👥 Sample users (first 5):")
        for user in users:
            print(f"   {user[0]}: Created {user[1]}, Last login {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying connection: {e}")

if __name__ == "__main__":
    test_azure_connection()
    verify_azure_vs_local()
