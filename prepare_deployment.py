#!/usr/bin/env python3
"""
Azure Deployment Preparation Script
Prepares the application for Azure deployment
"""

import os
import subprocess
import shutil
from pathlib import Path

def create_production_config():
    """Create production configuration file"""
    production_config = """
# Production Configuration for Azure
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Database configuration for Azure
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
    
    # User credentials
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    DEMO_USERNAME = os.environ.get('DEMO_USERNAME', 'demo')
    DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD')
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    
    # Protected users
    PROTECTED_USERS = ['bharath']
"""
    
    with open('production_config.py', 'w') as f:
        f.write(production_config)
    
    print("✅ Created production_config.py")

def prepare_git_commit():
    """Prepare files for Git commit"""
    print("🔧 Preparing Git commit...")
    
    # Files to definitely include
    important_files = [
        'admin/routes.py',
        'app.py', 
        'requirements.txt',
        'config.py',
        '.gitignore',
        'web.config',
        'production_config.py',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    # Files to exclude from commit
    exclude_files = [
        '.env',
        '*.db',
        '*_test.py',
        '*_debug.py',
        'inspect_*.py',
        'fix_*.py',
        'analyze_*.py',
        'reset_*.py',
        'test_*.py'
    ]
    
    print("\n📋 Files to be committed:")
    for file in important_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
    
    print("\n🚫 Files excluded from commit:")
    for pattern in exclude_files:
        print(f"   - {pattern}")
    
    return important_files

def check_azure_environment_variables():
    """Check if Azure environment variables are properly configured"""
    print("\n🔍 Azure Environment Variables Checklist")
    print("=" * 50)
    
    required_env_vars = [
        'ADMIN_PASSWORD',
        'DEMO_USERNAME', 
        'DEMO_PASSWORD',
        'FLASK_SECRET_KEY',
        'FLASK_ENV',
        'FLASK_DEBUG',
        'SESSION_TIMEOUT',
        'PASSWORD_MIN_LENGTH'
    ]
    
    print("⚠️  Make sure these are set in Azure App Service Configuration:")
    for var in required_env_vars:
        print(f"   - {var}")
    
    print("\n💡 To set these in Azure:")
    print("   1. Go to Azure Portal")
    print("   2. Find your App Service: ai-learning-tracker-bharath")
    print("   3. Go to Configuration > Application settings")
    print("   4. Add each environment variable")

def create_deployment_commands():
    """Create the Git commands for deployment"""
    print("\n🚀 Git Deployment Commands")
    print("=" * 30)
    
    commands = [
        "git add admin/routes.py app.py requirements.txt config.py .gitignore web.config production_config.py DEPLOYMENT_GUIDE.md",
        'git commit -m "Fix LinkedIn course addition and global learnings count\n\n- Added missing url, category, difficulty columns to courses table\n- Fixed LinkedIn course insertion logic\n- Updated admin learning entries to be properly marked as global\n- Added environment variable configuration\n- Enhanced security with .env file setup\n- Updated requirements.txt with python-dotenv"',
        "git push azure master"
    ]
    
    print("Run these commands to deploy:")
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i}. {cmd}")
    
    return commands

def check_deployment_readiness():
    """Check if the application is ready for deployment"""
    print("\n✅ Deployment Readiness Check")
    print("=" * 35)
    
    checks = []
    
    # Check if .gitignore exists and contains .env
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            if '.env' in gitignore_content:
                checks.append(("✅", ".env excluded from Git"))
            else:
                checks.append(("❌", ".env NOT excluded from Git"))
    else:
        checks.append(("❌", ".gitignore file missing"))
    
    # Check if important files exist
    important_files = ['admin/routes.py', 'app.py', 'requirements.txt', 'config.py']
    for file in important_files:
        if os.path.exists(file):
            checks.append(("✅", f"{file} exists"))
        else:
            checks.append(("❌", f"{file} missing"))
    
    # Check if sensitive files are excluded
    sensitive_files = ['.env', 'ai_learning.db']
    for file in sensitive_files:
        if os.path.exists(file):
            checks.append(("⚠️", f"{file} exists locally (will be excluded from commit)"))
    
    for status, message in checks:
        print(f"   {status} {message}")
    
    all_good = all(check[0] == "✅" for check in checks if check[0] != "⚠️")
    
    if all_good:
        print("\n🎉 Application is ready for deployment!")
    else:
        print("\n⚠️  Please fix the issues above before deploying")
    
    return all_good

def main():
    """Main deployment preparation function"""
    print("🚀 AI Learning Tracker - Azure Deployment Preparation")
    print("=" * 60)
    
    # Create production configuration
    create_production_config()
    
    # Prepare Git commit
    prepare_git_commit()
    
    # Check Azure environment variables
    check_azure_environment_variables()
    
    # Check deployment readiness
    ready = check_deployment_readiness()
    
    if ready:
        # Create deployment commands
        commands = create_deployment_commands()
        
        print("\n🎯 Next Steps:")
        print("1. Set environment variables in Azure App Service")
        print("2. Run the Git commands above")
        print("3. Monitor Azure deployment logs")
        print("4. Test the application after deployment")
    else:
        print("\n❌ Please fix the issues before proceeding with deployment")

if __name__ == "__main__":
    main()
