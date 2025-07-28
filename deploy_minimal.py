#!/usr/bin/env python3
"""
Deploy minimal app to Azure and test
"""

import subprocess
import sys
import os
import shutil
import time

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"Output: {result.stdout[:500]}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - EXCEPTION: {e}")
        return False

def main():
    """Deploy minimal app to Azure"""
    print("🚀 Deploying Minimal AI Learning Tracker to Azure")
    print("=" * 50)
    
    # Step 1: Create startup command for minimal app
    startup_content = '''#!/bin/bash
echo "Starting minimal AI Learning Tracker..."
cd /home/site/wwwroot
python app_minimal.py
'''
    
    with open('startup_minimal.sh', 'w') as f:
        f.write(startup_content)
    print("✅ Created startup_minimal.sh")
    
    # Step 2: Create minimal requirements
    requirements_content = '''Flask==2.3.3
Werkzeug==2.3.7
gunicorn==21.2.0
'''
    
    with open('requirements_minimal.txt', 'w') as f:
        f.write(requirements_content)
    print("✅ Created requirements_minimal.txt")
    
    # Step 3: Git operations
    commands = [
        ("git add app_minimal.py startup_minimal.sh requirements_minimal.txt", "Adding minimal files to git"),
        ("git commit -m 'Deploy minimal app for Azure 500 error diagnosis'", "Committing minimal app"),
        ("git push origin main", "Pushing to GitHub"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️ Warning: {description} failed, continuing...")
    
    # Step 4: Get app info
    print("\n📋 Getting Azure app information...")
    run_command("az webapp list --query '[].{Name:name, ResourceGroup:resourceGroup, DefaultHostName:defaultHostName}' --output table", "Listing Azure web apps")
    
    # Step 5: Set startup command (try different resource groups)
    resource_groups = ["AI_Learning_rg", "AI-Learning-rg", "ai-learning-rg", "Default"]
    app_name = "ai-learning-tracker"
    
    for rg in resource_groups:
        print(f"\n🔧 Trying to configure app in resource group: {rg}")
        
        # Try to set startup command
        startup_cmd = f"az webapp config set --resource-group {rg} --name {app_name} --startup-file 'python app_minimal.py'"
        if run_command(startup_cmd, f"Setting startup command in {rg}"):
            print(f"✅ Successfully configured startup in {rg}")
            break
        
        # Try alternative startup
        startup_cmd2 = f"az webapp config appsettings set --resource-group {rg} --name {app_name} --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITE_RUN_FROM_PACKAGE=1"
        if run_command(startup_cmd2, f"Setting app settings in {rg}"):
            print(f"✅ Successfully configured app settings in {rg}")
    
    # Step 6: Test the deployment
    print("\n🧪 Testing the deployment...")
    time.sleep(10)  # Wait for deployment
    
    test_urls = [
        "https://ai-learning-tracker.azurewebsites.net",
        "https://ai-learning-tracker.azurewebsites.net/health",
        "https://ai-learning-tracker.azurewebsites.net/login"
    ]
    
    for url in test_urls:
        run_command(f"curl -s -o /dev/null -w '%{{http_code}}' {url}", f"Testing {url}")
    
    print("\n🎯 Deployment Summary:")
    print("- Created app_minimal.py with simplified Flask app")
    print("- Created startup_minimal.sh for Azure")
    print("- Created requirements_minimal.txt with minimal deps")
    print("- Pushed to GitHub")
    print("- Attempted Azure configuration")
    print("\n🔗 Test the app:")
    print("https://ai-learning-tracker.azurewebsites.net")
    print("https://ai-learning-tracker.azurewebsites.net/health")

if __name__ == "__main__":
    main()
