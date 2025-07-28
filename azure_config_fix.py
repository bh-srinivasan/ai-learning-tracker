#!/usr/bin/env python3
"""
Azure App Service Configuration Checker and Fixer
Diagnose and fix Azure-specific deployment issues
"""

import requests
import json
import subprocess
import os

def get_azure_app_info():
    """Get Azure App Service information"""
    print("🔍 Checking Azure App Service Configuration...")
    
    app_name = "ai-learning-tracker-bharath"
    
    # Try to get app service configuration
    try:
        # Get general app info
        cmd = f"az webapp show --name {app_name} --resource-group Microsoft.StdApp2025 --query '{{state:state, defaultHostName:defaultHostName, kind:kind}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            app_info = json.loads(result.stdout)
            print(f"✅ App State: {app_info.get('state', 'Unknown')}")
            print(f"✅ Host Name: {app_info.get('defaultHostName', 'Unknown')}")
            print(f"✅ Kind: {app_info.get('kind', 'Unknown')}")
        else:
            print(f"⚠️ Could not get app info: {result.stderr}")
            
        # Get app settings
        cmd = f"az webapp config appsettings list --name {app_name} --resource-group Microsoft.StdApp2025"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            settings = json.loads(result.stdout)
            print(f"\n📋 Current App Settings ({len(settings)} total):")
            for setting in settings:
                if 'password' not in setting['name'].lower() and 'secret' not in setting['name'].lower():
                    print(f"  {setting['name']}: {setting['value']}")
                else:
                    print(f"  {setting['name']}: [HIDDEN]")
        else:
            print(f"⚠️ Could not get app settings: {result.stderr}")
            
        # Get startup command
        cmd = f"az webapp config show --name {app_name} --resource-group Microsoft.StdApp2025 --query appCommandLine"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            startup_cmd = result.stdout.strip().strip('"')
            print(f"\n🚀 Current Startup Command: {startup_cmd}")
        else:
            print(f"⚠️ Could not get startup command: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error checking Azure configuration: {e}")

def set_correct_startup_command():
    """Set the correct startup command for Azure"""
    print("\n🔧 Setting Correct Startup Command...")
    
    app_name = "ai-learning-tracker-bharath"
    
    # Try different startup commands
    startup_commands = [
        "python main.py",
        "gunicorn --bind=0.0.0.0 --timeout 600 main:app",
        "python application.py",
        "gunicorn --bind=0.0.0.0 --timeout 600 application:app"
    ]
    
    for i, cmd in enumerate(startup_commands, 1):
        print(f"\n🧪 Trying startup command {i}: {cmd}")
        
        try:
            # Set the startup command
            az_cmd = f'az webapp config set --name {app_name} --resource-group Microsoft.StdApp2025 --startup-file "{cmd}"'
            result = subprocess.run(az_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Set startup command: {cmd}")
                
                # Wait a moment for restart
                print("⏳ Waiting for app to restart...")
                import time
                time.sleep(30)
                
                # Test the app
                test_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
                try:
                    response = requests.get(test_url, timeout=60)
                    print(f"📊 Test result: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"🎉 SUCCESS with startup command: {cmd}")
                        return True
                    elif response.status_code != 500:
                        print(f"⚠️ Different error: {response.status_code}")
                    else:
                        print("❌ Still 500 error")
                        
                except Exception as e:
                    print(f"❌ Test failed: {e}")
                    
            else:
                print(f"❌ Failed to set startup command: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error setting startup command: {e}")
    
    return False

def set_azure_environment_variables():
    """Set critical environment variables in Azure"""
    print("\n🔧 Setting Azure Environment Variables...")
    
    app_name = "ai-learning-tracker-bharath"
    
    # Critical environment variables for production
    env_vars = {
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': 'False',
        'PYTHONPATH': '.',
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true',
        'ENABLE_ORYX_BUILD': 'true',
        'WEBSITES_ENABLE_APP_SERVICE_STORAGE': 'false',
        'PORT': '8000'
    }
    
    for key, value in env_vars.items():
        try:
            cmd = f'az webapp config appsettings set --name {app_name} --resource-group Microsoft.StdApp2025 --settings {key}="{value}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Set {key}={value}")
            else:
                print(f"❌ Failed to set {key}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error setting {key}: {e}")

def create_simple_test_app():
    """Create a simple test application to verify Azure is working"""
    print("\n🧪 Creating Simple Test Application...")
    
    simple_app = '''#!/usr/bin/env python3
"""
Simple test application for Azure debugging
"""

from flask import Flask
import os
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    return f"""
    <h1>Azure Test App Working!</h1>
    <p>Python version: {sys.version}</p>
    <p>Current directory: {os.getcwd()}</p>
    <p>Environment: {os.environ.get('FLASK_ENV', 'not set')}</p>
    <p>Files in directory: {os.listdir('.')[:10]}</p>
    """

@app.route('/health')
def health():
    return {"status": "ok", "message": "Simple app is working"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
'''
    
    with open('test_app.py', 'w') as f:
        f.write(simple_app)
    
    print("✅ Created test_app.py")
    
    return 'test_app.py'

def deploy_test_app():
    """Deploy and test the simple application"""
    print("\n🚀 Deploying Test Application...")
    
    # Create test app
    test_file = create_simple_test_app()
    
    # Commit and deploy
    try:
        subprocess.run('git add test_app.py', shell=True, check=True)
        subprocess.run('git commit -m "Add simple test app for Azure debugging"', shell=True, check=True)
        subprocess.run('git push azure master', shell=True, check=True)
        
        print("✅ Test app deployed")
        
        # Set startup command to use test app
        app_name = "ai-learning-tracker-bharath"
        cmd = f'az webapp config set --name {app_name} --resource-group Microsoft.StdApp2025 --startup-file "python test_app.py"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Set startup command to test app")
            
            # Wait and test
            import time
            time.sleep(30)
            
            response = requests.get("https://ai-learning-tracker-bharath.azurewebsites.net", timeout=60)
            if response.status_code == 200:
                print("🎉 Test app works! The issue is in the main application.")
                return True
            else:
                print(f"❌ Test app also fails: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to set test startup command: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying test app: {e}")
        return False

def main():
    """Run comprehensive Azure diagnostics and fixes"""
    print("🔧 Azure App Service Comprehensive Fix")
    print("=" * 50)
    
    # Step 1: Check current configuration
    get_azure_app_info()
    
    # Step 2: Set environment variables
    set_azure_environment_variables()
    
    # Step 3: Try different startup commands
    if set_correct_startup_command():
        print("\n🎉 SUCCESS! Application is now working!")
        return True
    
    # Step 4: If main app still fails, test with simple app
    print("\n🧪 Main app still failing, testing with simple app...")
    if deploy_test_app():
        print("\n💡 Azure infrastructure works, issue is in main application code")
        print("Reverting to main app with better error handling...")
        
        # Set back to main app but with better startup command
        app_name = "ai-learning-tracker-bharath"
        cmd = f'az webapp config set --name {app_name} --resource-group Microsoft.StdApp2025 --startup-file "python main.py"'
        subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
    print("\n📋 SUMMARY:")
    print("- Azure App Service configuration updated")
    print("- Environment variables set")
    print("- Multiple startup commands tested")
    print("- Check Azure App Service logs for detailed error messages")
    
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
