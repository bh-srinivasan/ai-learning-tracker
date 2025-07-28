#!/usr/bin/env python3
"""
Azure 500 Error Diagnostic Script
Comprehensive diagnosis and fix for Azure App Service 500 errors
"""

import os
import subprocess
import json
import requests
from datetime import datetime, timedelta
import time

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_azure_app_service_logs():
    """Check Azure App Service logs for error details"""
    print("🔍 Checking Azure App Service logs...")
    
    # Try to get Azure CLI logs
    app_name = "ai-learning-tracker-bharath"
    resource_group = "your-resource-group"  # May need to be configured
    
    print(f"Attempting to retrieve logs for app: {app_name}")
    
    # Check if Azure CLI is available
    success, stdout, stderr = run_command("az --version")
    if success:
        print("✅ Azure CLI is available")
        
        # Get recent logs
        log_command = f'az webapp log tail --name {app_name} --resource-group {resource_group} --logs application'
        success, logs, error = run_command(log_command)
        
        if success and logs:
            print("📋 Recent Application Logs:")
            print(logs[-2000:])  # Last 2000 characters
            return logs
        else:
            print(f"⚠️ Could not retrieve logs via Azure CLI: {error}")
    else:
        print("⚠️ Azure CLI not available or not logged in")
    
    # Alternative: Check local deployment logs
    print("\n📂 Checking local deployment artifacts...")
    return None

def test_azure_app_connectivity():
    """Test if the Azure app is accessible and what error it returns"""
    print("\n🌐 Testing Azure App Connectivity...")
    
    app_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    try:
        print(f"Testing: {app_url}")
        response = requests.get(app_url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 500:
            print("❌ Confirmed 500 Internal Server Error")
            
            # Check if there's any useful error info in response
            content = response.text[:1000]  # First 1000 chars
            print(f"Response Content Preview:\n{content}")
            
            return {
                'status_code': 500,
                'content': content,
                'headers': dict(response.headers)
            }
        else:
            print(f"✅ App responded with status: {response.status_code}")
            return {
                'status_code': response.status_code,
                'content': response.text[:500],
                'headers': dict(response.headers)
            }
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - app may be unresponsive")
        return {'error': 'timeout'}
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return {'error': 'connection_error', 'details': str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {'error': 'unexpected', 'details': str(e)}

def check_environment_variables():
    """Check critical environment variables and configuration"""
    print("\n🔧 Checking Environment Variables and Configuration...")
    
    # Check if we have a .env file or config
    env_files = ['.env', 'config.py', 'azure_storage_config.example']
    config_issues = []
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ Found {env_file}")
            
            # Read and check for critical variables
            with open(env_file, 'r') as f:
                content = f.read()
                
                # Check for database configuration
                if 'database' in content.lower() or 'db' in content.lower():
                    print(f"  📄 {env_file} contains database configuration")
                
                # Check for Azure-specific config
                if 'azure' in content.lower():
                    print(f"  ☁️ {env_file} contains Azure configuration")
                    
        else:
            print(f"⚠️ {env_file} not found")
    
    # Check app.py for environment variable usage
    if os.path.exists('app.py'):
        with open('app.py', 'r') as f:
            app_content = f.read()
            
            # Look for environment variable usage
            import re
            env_vars = re.findall(r'os\.environ\.get\([\'"]([^\'"]+)[\'"]', app_content)
            env_vars.extend(re.findall(r'os\.getenv\([\'"]([^\'"]+)[\'"]', app_content))
            
            if env_vars:
                print(f"\n📋 Environment variables used in app.py:")
                for var in set(env_vars):
                    print(f"  - {var}")
                    
                # Check for critical missing variables
                critical_vars = ['SECRET_KEY', 'DATABASE_URL', 'ADMIN_PASSWORD', 'DEMO_PASSWORD']
                missing_critical = [var for var in critical_vars if var in env_vars]
                
                if missing_critical:
                    print(f"\n⚠️ Critical environment variables that may be missing in Azure:")
                    for var in missing_critical:
                        print(f"  - {var}")
                    config_issues.extend(missing_critical)
    
    return config_issues

def check_database_connectivity():
    """Check database configuration and connectivity"""
    print("\n🗄️ Checking Database Configuration...")
    
    db_issues = []
    
    # Check for database files and configuration
    db_files = ['ai_learning.db', 'database_environment_manager.py']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"✅ Found {db_file}")
            
            if db_file.endswith('.db'):
                # Check SQLite database size and accessibility
                try:
                    size = os.path.getsize(db_file)
                    print(f"  📊 Database size: {size} bytes")
                    
                    if size == 0:
                        print(f"  ❌ Database file is empty!")
                        db_issues.append(f"{db_file} is empty")
                    
                except Exception as e:
                    print(f"  ❌ Error accessing database: {e}")
                    db_issues.append(f"Cannot access {db_file}: {e}")
        else:
            print(f"⚠️ {db_file} not found")
            if db_file.endswith('.db'):
                db_issues.append(f"Missing database file: {db_file}")
    
    # Check database_environment_manager.py for Azure SQL configuration
    if os.path.exists('database_environment_manager.py'):
        with open('database_environment_manager.py', 'r') as f:
            db_manager_content = f.read()
            
            if 'azure' in db_manager_content.lower():
                print("  ☁️ Database manager supports Azure SQL")
            
            if 'sqlite' in db_manager_content.lower():
                print("  📁 Database manager supports SQLite")
    
    return db_issues

def check_python_dependencies():
    """Check Python dependencies and requirements"""
    print("\n📦 Checking Python Dependencies...")
    
    dependency_issues = []
    
    if os.path.exists('requirements.txt'):
        print("✅ Found requirements.txt")
        
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
            
        print(f"📋 Requirements ({len(requirements)} packages):")
        for req in requirements[:10]:  # Show first 10
            if req.strip():
                print(f"  - {req.strip()}")
        
        if len(requirements) > 10:
            print(f"  ... and {len(requirements) - 10} more")
        
        # Check for common problematic packages
        problematic = ['sqlite3', 'pyodbc']
        for req in requirements:
            for prob in problematic:
                if prob in req.lower():
                    print(f"  ⚠️ Potentially problematic for Azure: {req}")
                    dependency_issues.append(f"Problematic dependency: {req}")
    else:
        print("❌ requirements.txt not found!")
        dependency_issues.append("Missing requirements.txt")
    
    return dependency_issues

def analyze_app_py_for_issues():
    """Analyze app.py for common Azure deployment issues"""
    print("\n🔍 Analyzing app.py for Common Issues...")
    
    app_issues = []
    
    if not os.path.exists('app.py'):
        print("❌ app.py not found!")
        return ["Missing app.py"]
    
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Check for common issues
    issues_to_check = [
        ('app.run(debug=True)', 'Debug mode enabled in production'),
        ('app.run(host=', 'Hardcoded host configuration'),
        ('localhost', 'Localhost references that won\'t work in Azure'),
        ('127.0.0.1', 'Local IP references that won\'t work in Azure'),
        ('sqlite:////', 'SQLite absolute path that may not work in Azure'),
        ('open(', 'File operations that may fail due to read-only filesystem'),
    ]
    
    for pattern, issue_desc in issues_to_check:
        if pattern in app_content:
            print(f"  ⚠️ Found: {issue_desc}")
            app_issues.append(issue_desc)
    
    # Check for proper WSGI setup
    if 'if __name__ == "__main__"' in app_content:
        print("  ✅ Found main guard")
    else:
        print("  ⚠️ No main guard found")
        app_issues.append("Missing if __name__ == '__main__' guard")
    
    # Check for error handling
    if '@app.errorhandler' in app_content:
        print("  ✅ Found error handlers")
    else:
        print("  ⚠️ No error handlers found")
        app_issues.append("Missing error handlers for better debugging")
    
    return app_issues

def create_azure_fix_script():
    """Create a comprehensive fix script for common Azure issues"""
    print("\n🛠️ Creating Azure Fix Script...")
    
    fix_script = """#!/usr/bin/env python3
'''
Azure Deployment Fix Script
Fixes common issues that cause 500 errors in Azure App Service
'''

import os
import sys
import sqlite3
from datetime import datetime

def fix_database_issues():
    '''Fix database-related issues'''
    print("🗄️ Fixing database issues...")
    
    # Ensure database file exists and is not empty
    db_file = 'ai_learning.db'
    if not os.path.exists(db_file) or os.path.getsize(db_file) == 0:
        print(f"Creating/initializing {db_file}...")
        
        # Create a basic database structure
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create basic tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT,
                description TEXT,
                level TEXT,
                category TEXT,
                duration TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_title TEXT NOT NULL,
                learning_notes TEXT,
                completion_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create upload reports tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS excel_upload_reports (
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
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS excel_upload_row_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER,
                row_number INTEGER,
                status TEXT,
                message TEXT,
                course_title TEXT,
                course_url TEXT,
                FOREIGN KEY (report_id) REFERENCES excel_upload_reports (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database {db_file} created and initialized")
    else:
        print(f"✅ Database {db_file} exists and has content")

def fix_environment_variables():
    '''Set up proper environment variables for Azure'''
    print("🔧 Setting up environment variables...")
    
    # Set default values for missing environment variables
    env_defaults = {
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': 'False',
        'SECRET_KEY': 'your-secret-key-change-in-production',
        'DATABASE_URL': 'sqlite:///ai_learning.db',
    }
    
    for key, default_value in env_defaults.items():
        if not os.environ.get(key):
            os.environ[key] = default_value
            print(f"  Set {key} to default value")
        else:
            print(f"  ✅ {key} is already set")

def create_wsgi_file():
    '''Create proper WSGI file for Azure deployment'''
    print("📄 Creating WSGI configuration...")
    
    wsgi_content = '''
WSGI Configuration for Azure App Service
'''
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run()
'''
    
    with open('main.py', 'w') as f:
        f.write(wsgi_content)
    
    print("✅ Created main.py for WSGI")

def main():
    '''Run all fixes'''
    print("🔧 Azure Deployment Fix Script")
    print("=" * 50)
    
    fix_database_issues()
    fix_environment_variables()
    create_wsgi_file()
    
    print("\\n✅ All fixes applied!")
    print("💡 Next steps:")
    print("1. Commit and push changes")
    print("2. Redeploy to Azure")
    print("3. Check Application Settings in Azure Portal")
    print("4. Monitor logs after deployment")

if __name__ == "__main__":
    main()
"""
    
    with open('azure_deployment_fix.py', 'w') as f:
        f.write(fix_script)
    
    print("✅ Created azure_deployment_fix.py")

def main():
    """Main diagnostic and fix process"""
    print("🚨 Azure 500 Error Diagnostic Script")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    
    all_issues = []
    
    # Step 1: Test app connectivity
    connectivity_result = test_azure_app_connectivity()
    
    # Step 2: Check logs
    logs = check_azure_app_service_logs()
    
    # Step 3: Check environment variables
    env_issues = check_environment_variables()
    all_issues.extend(env_issues)
    
    # Step 4: Check database
    db_issues = check_database_connectivity()
    all_issues.extend(db_issues)
    
    # Step 5: Check dependencies
    dep_issues = check_python_dependencies()
    all_issues.extend(dep_issues)
    
    # Step 6: Analyze app.py
    app_issues = analyze_app_py_for_issues()
    all_issues.extend(app_issues)
    
    # Step 7: Create fix script
    create_azure_fix_script()
    
    # Summary
    print("\\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if all_issues:
        print(f"❌ Found {len(all_issues)} issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✅ No obvious configuration issues found")
    
    print("\\n🛠️ RECOMMENDED ACTIONS:")
    print("1. Run the azure_deployment_fix.py script")
    print("2. Check Azure App Service Configuration in Portal")
    print("3. Verify environment variables are set in Azure")
    print("4. Redeploy the application")
    print("5. Monitor Azure App Service logs")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
