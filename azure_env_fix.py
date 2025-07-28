#!/usr/bin/env python3
"""
Azure Environment Configuration Fix
Specifically addresses Azure App Service environment issues
"""

import os
import json

def create_azure_startup_command():
    """Create the correct startup command for Azure"""
    print("🚀 Creating Azure Startup Command...")
    
    # Azure App Service expects a specific startup command
    # The issue might be that it's trying to run app.py directly instead of using WSGI
    
    startup_commands = {
        'gunicorn': 'python -m gunicorn --bind=0.0.0.0 --timeout 600 main:app',
        'direct': 'python main.py',
        'module': 'python -m app'
    }
    
    # Create startup command file for Azure
    with open('startup_command.txt', 'w') as f:
        f.write(startup_commands['gunicorn'])
    
    print("✅ Created startup_command.txt with gunicorn")
    
    return startup_commands['gunicorn']

def create_azure_main_py():
    """Create a proper main.py that works with Azure"""
    print("📄 Creating Azure-optimized main.py...")
    
    main_content = '''#!/usr/bin/env python3
"""
Azure App Service Entry Point
Optimized for Azure App Service deployment
"""

import os
import sys
import logging

# Configure logging for Azure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

logger.info(f"Starting application from: {current_dir}")
logger.info(f"Python path: {sys.path[:3]}")

try:
    # Set environment for Azure
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('FLASK_DEBUG', 'False')
    
    logger.info("Environment variables set")
    
    # Import the Flask app
    from app import app
    
    logger.info("App imported successfully")
    
    # Configure for production
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    app.config['TESTING'] = False
    
    # Set secret key if not provided
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-me')
    
    logger.info("App configured for production")
    
    # Log some basic info
    logger.info(f"App name: {app.name}")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Environment: {app.config.get('ENV')}")
    
    # Test that the app can handle requests
    with app.test_request_context():
        logger.info("Test request context works")
    
    logger.info("App initialization complete")
    
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Files in directory: {os.listdir('.')}")
    raise
except Exception as e:
    logger.error(f"Error during app initialization: {e}")
    raise

# For direct execution
if __name__ == "__main__":
    logger.info("Running app directly")
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=False
    )
else:
    logger.info("App loaded for WSGI server")

# Export for WSGI
application = app
'''
    
    with open('main.py', 'w') as f:
        f.write(main_content)
    
    print("✅ Created Azure-optimized main.py")

def create_azure_web_config():
    """Create web.config for Azure App Service"""
    print("⚙️ Creating web.config for Azure...")
    
    web_config = '''<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="python" 
                  arguments="main.py" 
                  stdoutLogEnabled="true" 
                  stdoutLogFile="logs\\stdout.log"
                  startupTimeLimit="60"
                  requestTimeout="04:00:00">
      <environmentVariables>
        <environmentVariable name="PYTHONPATH" value="." />
        <environmentVariable name="FLASK_ENV" value="production" />
        <environmentVariable name="FLASK_DEBUG" value="False" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>'''
    
    with open('web.config', 'w') as f:
        f.write(web_config)
    
    print("✅ Created web.config")

def create_application_py():
    """Create application.py as an alternative entry point"""
    print("📄 Creating application.py entry point...")
    
    app_content = '''#!/usr/bin/env python3
"""
Alternative entry point for Azure App Service
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set production environment
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Import and configure the app
from app import app

app.config['DEBUG'] = False
app.config['ENV'] = 'production'

# This is what Azure will look for
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=False)
'''
    
    with open('application.py', 'w') as f:
        f.write(app_content)
    
    print("✅ Created application.py")

def check_requirements_for_azure():
    """Check and fix requirements.txt for Azure compatibility"""
    print("📦 Checking requirements.txt for Azure...")
    
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip()
        
        # Check if gunicorn is included
        if 'gunicorn' not in requirements.lower():
            print("Adding gunicorn to requirements...")
            with open('requirements.txt', 'a') as f:
                f.write('\ngunicorn==21.2.0\n')
            print("✅ Added gunicorn to requirements.txt")
        else:
            print("✅ gunicorn already in requirements.txt")
    else:
        print("❌ requirements.txt not found!")

def create_azure_deployment_script():
    """Create a script to set Azure environment variables"""
    print("🔧 Creating Azure deployment configuration...")
    
    azure_config = '''#!/bin/bash
# Azure App Service Configuration Script
# Run this to configure Azure environment variables

echo "Configuring Azure App Service..."

# Set startup command
az webapp config set --name ai-learning-tracker-bharath --resource-group your-resource-group --startup-file "python main.py"

# Set application settings
az webapp config appsettings set --name ai-learning-tracker-bharath --resource-group your-resource-group --settings \\
    FLASK_ENV=production \\
    FLASK_DEBUG=False \\
    PYTHONPATH=. \\
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \\
    ENABLE_ORYX_BUILD=true

echo "Azure configuration complete!"
echo "Note: Update the resource group name in this script"
'''
    
    with open('configure_azure.sh', 'w') as f:
        f.write(azure_config)
    
    print("✅ Created configure_azure.sh")

def create_runtime_txt():
    """Create runtime.txt to specify Python version"""
    print("🐍 Creating runtime.txt...")
    
    with open('runtime.txt', 'w') as f:
        f.write('python-3.9\n')
    
    print("✅ Created runtime.txt with Python 3.9")

def main():
    """Run all Azure fixes"""
    print("🔧 Azure Environment Configuration Fix")
    print("=" * 50)
    
    # Create all necessary files for Azure deployment
    create_azure_main_py()
    create_application_py()
    create_azure_web_config()
    create_azure_startup_command()
    check_requirements_for_azure()
    create_runtime_txt()
    create_azure_deployment_script()
    
    print("\n✅ Azure Environment Fix Complete!")
    print("\n🚀 Deployment Instructions:")
    print("1. Commit and push all changes:")
    print("   git add .")
    print("   git commit -m 'Fix Azure App Service configuration'")
    print("   git push origin master")
    print("   git push azure master")
    print("\n2. Optional: Configure Azure settings with configure_azure.sh")
    print("\n3. Monitor deployment logs in Azure Portal")
    print("\n4. Test the application after deployment")
    
    print("\n📋 Files created/modified:")
    files = ['main.py', 'application.py', 'web.config', 'startup_command.txt', 
             'requirements.txt', 'runtime.txt', 'configure_azure.sh']
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (failed to create)")

if __name__ == "__main__":
    main()
