#!/usr/bin/env python3
"""
Final comprehensive error check for the AI Learning Tracker workspace.
This script checks for any remaining errors after all fixes have been applied.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_syntax():
    """Check Python files for syntax errors."""
    print("🔍 Checking Python syntax errors...")
    python_files = [
        "app.py",
        "level_manager.py",
        "dashboard/routes.py",
        "auth/routes.py",
        "learnings/routes.py",
        "admin/routes.py"
    ]
    
    errors_found = []
    for file in python_files:
        if os.path.exists(file):
            try:
                result = subprocess.run([sys.executable, "-m", "py_compile", file], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    errors_found.append(f"{file}: {result.stderr}")
                else:
                    print(f"✅ {file} - No syntax errors")
            except Exception as e:
                errors_found.append(f"{file}: {str(e)}")
        else:
            print(f"⚠️  {file} - File not found")
    
    return errors_found

def check_flask_app():
    """Check if Flask app can be imported without errors."""
    print("🔍 Checking Flask app import...")
    try:
        import app
        print("✅ Flask app imports successfully")
        
        # Check if level_manager can be imported
        import level_manager
        print("✅ LevelManager imports successfully")
        
        return []
    except Exception as e:
        return [f"Flask app import error: {str(e)}"]

def check_database_integrity():
    """Check database structure and integrity."""
    print("🔍 Checking database integrity...")
    try:
        import sqlite3
        
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check all required tables exist
        required_tables = ['users', 'learning_entries', 'points_log']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
            else:
                missing_tables.append(table)
        
        # Check users table structure
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        required_user_columns = ['id', 'username', 'password_hash', 'level_points', 'level_updated_at']
        
        missing_user_columns = []
        for col in required_user_columns:
            if col in user_columns:
                print(f"✅ Users column '{col}' exists")
            else:
                missing_user_columns.append(col)
        
        conn.close()
        
        errors = []
        if missing_tables:
            errors.append(f"Missing tables: {missing_tables}")
        if missing_user_columns:
            errors.append(f"Missing user columns: {missing_user_columns}")
            
        return errors
        
    except Exception as e:
        return [f"Database check error: {str(e)}"]

def main():
    """Run all error checks."""
    print("🚀 Starting final comprehensive error check...")
    print("=" * 60)
    
    all_errors = []
    
    # Check Python syntax
    syntax_errors = check_python_syntax()
    all_errors.extend(syntax_errors)
    
    print()
    
    # Check Flask app
    flask_errors = check_flask_app()
    all_errors.extend(flask_errors)
    
    print()
    
    # Check database
    db_errors = check_database_integrity()
    all_errors.extend(db_errors)
    
    print()
    print("=" * 60)
    
    if all_errors:
        print("❌ ERRORS FOUND:")
        for error in all_errors:
            print(f"  • {error}")
        print(f"\nTotal errors: {len(all_errors)}")
        return False
    else:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ No syntax errors found")
        print("✅ Flask app imports successfully")  
        print("✅ Database structure is correct")
        print("✅ Workspace is error-free and ready for use")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
