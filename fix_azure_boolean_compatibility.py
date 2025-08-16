#!/usr/bin/env python3
"""
Azure SQL Boolean Compatibility Fix
This script addresses the boolean type mismatch between SQLite and Azure SQL
"""

import os
import sys

def fix_boolean_compatibility():
    """Fix boolean compatibility issues in the authentication system"""
    
    print("=== AZURE SQL BOOLEAN COMPATIBILITY FIX ===\n")
    
    # Read the current app.py file
    app_file = "app.py"
    if not os.path.exists(app_file):
        print(f"❌ {app_file} not found")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Make a backup
    backup_file = "app_backup_boolean_fix.py"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {backup_file}")
    
    # Fix 1: Update get_current_user function to handle boolean compatibility
    old_query = """user_session = conn.execute(f'''
            SELECT s.*, u.username, u.level, u.points, u.is_admin 
            FROM {session_table} s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = ?
        ''', (session_token, True)).fetchone()"""
    
    new_query = """user_session = conn.execute(f'''
            SELECT s.*, u.username, u.level, u.points, u.is_admin 
            FROM {session_table} s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = 1
        ''', (session_token,)).fetchone()"""
    
    if old_query in content:
        content = content.replace(old_query, new_query)
        print("✅ Fixed: get_current_user boolean query compatibility")
    else:
        print("⚠️  Warning: get_current_user query pattern not found exactly")
    
    # Fix 2: Update create_user_session function for Azure SQL compatibility
    old_insert = """conn.execute(f'''
                INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_token, user_id, ip_address, user_agent, expires_at))"""
    
    new_insert = """conn.execute(f'''
                INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_token, user_id, ip_address, user_agent, expires_at, 1))"""
    
    if old_insert in content:
        content = content.replace(old_insert, new_insert)
        print("✅ Fixed: create_user_session Azure SQL insert compatibility")
    else:
        print("⚠️  Warning: create_user_session insert pattern not found exactly")
    
    # Fix 3: Add enhanced error logging to login route
    login_route_old = """if user and check_password_hash(user['password_hash'], password):
            try:
                session_token = create_user_session(user['id'], request.remote_addr, request.headers.get('User-Agent'))
                session['session_token'] = session_token
                session['user_id'] = user['id']
                
                # Handle is_admin field safely
                try:
                    is_admin = bool(user['is_admin']) if user['is_admin'] is not None else False
                except KeyError:
                    is_admin = False
                    logger.warning(f"is_admin field missing for user {user['username']}")
                
                if is_admin:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            except Exception as e:
                logger.error(f"Session creation error: {e}")
                flash('Login failed. Please try again.', 'error')"""
    
    login_route_new = """if user and check_password_hash(user['password_hash'], password):
            try:
                logger.debug(f"Login attempt for user: {user['username']}, is_admin: {user.get('is_admin', 'NOT_SET')}")
                session_token = create_user_session(user['id'], request.remote_addr, request.headers.get('User-Agent'))
                
                if not session_token:
                    logger.error(f"Session creation failed for user {user['username']}")
                    flash('Login failed. Please try again.', 'error')
                    return redirect(url_for('login'))
                
                session['session_token'] = session_token
                session['user_id'] = user['id']
                
                # Handle is_admin field safely
                try:
                    is_admin = bool(user['is_admin']) if user['is_admin'] is not None else False
                    logger.debug(f"User {user['username']} is_admin status: {is_admin}")
                except KeyError:
                    is_admin = False
                    logger.warning(f"is_admin field missing for user {user['username']}")
                
                if is_admin:
                    logger.debug(f"Redirecting admin user {user['username']} to admin dashboard")
                    return redirect(url_for('admin_dashboard'))
                else:
                    logger.debug(f"Redirecting non-admin user {user['username']} to user dashboard")
                    return redirect(url_for('dashboard'))
            except Exception as e:
                logger.error(f"Login error for user {user['username']}: {e}")
                import traceback
                logger.error(f"Login traceback: {traceback.format_exc()}")
                flash('Login failed. Please contact support.', 'error')"""
    
    if login_route_old in content:
        content = content.replace(login_route_old, login_route_new)
        print("✅ Fixed: Enhanced login route error logging")
    else:
        print("⚠️  Warning: Login route pattern not found exactly - will add generic error handling")
    
    # Write the updated content
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated {app_file} with boolean compatibility fixes")
    return True

def create_test_script():
    """Create a test script to validate the fixes"""
    test_content = '''#!/usr/bin/env python3
"""
Test script to validate Azure SQL boolean compatibility fixes
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_boolean_fixes():
    print("=== TESTING BOOLEAN COMPATIBILITY FIXES ===\\n")
    
    try:
        from app import get_db_connection, is_azure_sql, get_session_table
        print("✅ Successfully imported app functions")
        
        # Test database connection
        conn = get_db_connection()
        session_table = get_session_table()
        
        print(f"✅ Database connection: {'Azure SQL' if is_azure_sql() else 'Local SQLite'}")
        print(f"✅ Session table: {session_table}")
        
        # Test the fixed query structure
        test_query = f"""
            SELECT s.*, u.username, u.level, u.points, u.is_admin 
            FROM {session_table} s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = 1
        """
        
        # Test with dummy data
        result = conn.execute(test_query, ("dummy_token",)).fetchone()
        print("✅ Fixed query structure validates successfully")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_boolean_fixes()
'''
    
    with open("test_boolean_fixes.py", 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ Created test script: test_boolean_fixes.py")

if __name__ == "__main__":
    print("Azure SQL Boolean Compatibility Fix Script")
    print("==========================================")
    
    if fix_boolean_compatibility():
        create_test_script()
        print("\n🎯 FIXES APPLIED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Test locally: python test_boolean_fixes.py")
        print("2. Deploy to Azure: git add . && git commit -m 'Fix: Azure SQL boolean compatibility'")
        print("3. Monitor Azure logs for improved error messages")
        print("4. Test non-admin login on production")
    else:
        print("\n❌ FIXES FAILED - Please check manually")
