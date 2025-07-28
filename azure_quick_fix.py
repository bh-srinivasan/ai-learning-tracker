#!/usr/bin/env python3
"""
Quick Azure 500 Error Fix Script
Focuses on the most common issues causing 500 errors
"""

import os
import subprocess
import requests
from datetime import datetime

def test_app_status():
    """Test the current app status"""
    print("🌐 Testing Azure App Status...")
    
    try:
        response = requests.get("https://ai-learning-tracker-bharath.azurewebsites.net", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ Confirmed 500 Internal Server Error")
            return True
        else:
            print(f"✅ App is responding with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return True

def check_critical_files():
    """Check for critical files that might be missing"""
    print("\n📁 Checking Critical Files...")
    
    critical_files = {
        'app.py': 'Main application file',
        'requirements.txt': 'Python dependencies',
        'ai_learning.db': 'SQLite database',
        'database_environment_manager.py': 'Database manager'
    }
    
    missing_files = []
    
    for file, description in critical_files.items():
        if os.path.exists(file):
            print(f"✅ {file} - {description}")
            
            # Check file size
            size = os.path.getsize(file)
            if size == 0:
                print(f"  ⚠️ {file} is empty!")
                missing_files.append(f"{file} is empty")
            elif file == 'ai_learning.db' and size < 1000:
                print(f"  ⚠️ Database seems very small ({size} bytes)")
                missing_files.append(f"Database may be corrupted or incomplete")
        else:
            print(f"❌ {file} - {description} - MISSING")
            missing_files.append(file)
    
    return missing_files

def fix_database_issues():
    """Fix common database issues"""
    print("\n🗄️ Fixing Database Issues...")
    
    db_file = 'ai_learning.db'
    
    # Check if database exists and has proper structure
    if not os.path.exists(db_file) or os.path.getsize(db_file) < 1000:
        print("Creating/fixing database...")
        
        import sqlite3
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Create essential tables
            tables = [
                '''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''',
                
                '''CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT,
                    description TEXT,
                    level TEXT,
                    category TEXT,
                    duration TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''',
                
                '''CREATE TABLE IF NOT EXISTS learning_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    course_title TEXT NOT NULL,
                    learning_notes TEXT,
                    completion_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''',
                
                '''CREATE TABLE IF NOT EXISTS excel_upload_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT NOT NULL,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_rows INTEGER DEFAULT 0,
                    processed_rows INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    warnings_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''',
                
                '''CREATE TABLE IF NOT EXISTS excel_upload_row_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER,
                    row_number INTEGER,
                    status TEXT,
                    message TEXT,
                    course_title TEXT,
                    course_url TEXT,
                    FOREIGN KEY (report_id) REFERENCES excel_upload_reports (id)
                )'''
            ]
            
            for table_sql in tables:
                cursor.execute(table_sql)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Database {db_file} created/fixed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing database: {e}")
            return False
    else:
        print(f"✅ Database {db_file} exists and appears healthy")
        return True

def create_wsgi_entry_point():
    """Create a proper WSGI entry point for Azure"""
    print("\n📄 Creating WSGI Entry Point...")
    
    wsgi_content = '''"""
WSGI Entry Point for Azure App Service
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    
    # Set production settings
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=8000)
        
except Exception as e:
    print(f"Error importing app: {e}")
    raise
'''
    
    with open('main.py', 'w') as f:
        f.write(wsgi_content)
    
    print("✅ Created main.py WSGI entry point")

def check_app_py_syntax():
    """Check if app.py has syntax errors"""
    print("\n🔍 Checking app.py Syntax...")
    
    try:
        result = subprocess.run(['python', '-m', 'py_compile', 'app.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ app.py syntax is valid")
            return True
        else:
            print(f"❌ Syntax error in app.py: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

def run_local_test():
    """Try to run the app locally to identify issues"""
    print("\n🧪 Testing Local App Import...")
    
    try:
        # Try to import the app
        import sys
        sys.path.insert(0, '.')
        
        from app import app
        print("✅ App imports successfully")
        
        # Check if app has routes
        if hasattr(app, 'url_map') and app.url_map._rules:
            print(f"✅ App has {len(app.url_map._rules)} routes configured")
        else:
            print("⚠️ App has no routes configured")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def create_startup_command():
    """Create proper startup command for Azure"""
    print("\n🚀 Creating Startup Configuration...")
    
    # Create a simple startup command file
    startup_content = 'python main.py'
    
    with open('startup.txt', 'w') as f:
        f.write(startup_content)
    
    print("✅ Created startup.txt with: python main.py")
    
    # Also create a web.config for Azure
    web_config = '''<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="python" arguments="main.py" stdoutLogEnabled="true" stdoutLogFile="logs\\stdout.log">
      <environmentVariables>
        <environmentVariable name="PYTHONPATH" value="." />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>'''
    
    with open('web.config', 'w') as f:
        f.write(web_config)
    
    print("✅ Created web.config for Azure")

def main():
    """Run the quick fix process"""
    print("🔧 Azure 500 Error Quick Fix")
    print("=" * 40)
    print(f"Timestamp: {datetime.now()}")
    
    # Step 1: Confirm the error
    has_500_error = test_app_status()
    
    if not has_500_error:
        print("\n✅ App appears to be working!")
        return True
    
    # Step 2: Check critical files
    missing_files = check_critical_files()
    
    # Step 3: Fix database
    db_fixed = fix_database_issues()
    
    # Step 4: Check syntax
    syntax_ok = check_app_py_syntax()
    
    # Step 5: Test local import
    import_ok = run_local_test()
    
    # Step 6: Create WSGI entry point
    create_wsgi_entry_point()
    
    # Step 7: Create startup configuration
    create_startup_command()
    
    print("\n" + "=" * 40)
    print("📋 FIX SUMMARY")
    print("=" * 40)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
    else:
        print("✅ All critical files present")
    
    print(f"Database: {'✅ Fixed/OK' if db_fixed else '❌ Issues remain'}")
    print(f"Syntax: {'✅ Valid' if syntax_ok else '❌ Errors found'}")
    print(f"Import: {'✅ Works' if import_ok else '❌ Failed'}")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Commit and push these fixes")
    print("2. Redeploy to Azure")
    print("3. Test the application")
    
    return len(missing_files) == 0 and db_fixed and syntax_ok and import_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
