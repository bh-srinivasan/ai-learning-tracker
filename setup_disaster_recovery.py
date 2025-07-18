"""
Azure Configuration and Testing Scripts
=======================================

Scripts to configure Azure services and test backup/restore functionality
"""

import os
import json
import subprocess
import sys
from typing import Dict, Any

def create_azure_resources_script():
    """Create Azure CLI script for setting up backup resources"""
    script = '''#!/bin/bash

# Azure Resource Setup for AI Learning Tracker Backup System
# ===========================================================

set -e  # Exit on any error

# Configuration
RESOURCE_GROUP="ai-learning-rg"
STORAGE_ACCOUNT="ailearningbackups$(date +%s)"  # Unique name
LOCATION="East US"
CONTAINER_NAME="ai-learning-backups"

echo "=== Setting up Azure resources for backup system ==="

# Login to Azure (if not already logged in)
echo "Checking Azure login status..."
az account show > /dev/null 2>&1 || {
    echo "Please login to Azure first:"
    echo "az login"
    exit 1
}

# Create resource group if it doesn't exist
echo "Creating resource group: $RESOURCE_GROUP"
az group create \\
    --name $RESOURCE_GROUP \\
    --location "$LOCATION" \\
    --output table

# Create storage account with geo-redundant storage
echo "Creating storage account: $STORAGE_ACCOUNT"
az storage account create \\
    --name $STORAGE_ACCOUNT \\
    --resource-group $RESOURCE_GROUP \\
    --location "$LOCATION" \\
    --sku Standard_GRS \\
    --kind StorageV2 \\
    --access-tier Hot \\
    --https-only true \\
    --min-tls-version TLS1_2 \\
    --output table

# Get storage account connection string
echo "Getting storage account connection string..."
CONNECTION_STRING=$(az storage account show-connection-string \\
    --name $STORAGE_ACCOUNT \\
    --resource-group $RESOURCE_GROUP \\
    --output tsv)

# Create blob container
echo "Creating blob container: $CONTAINER_NAME"
az storage container create \\
    --name $CONTAINER_NAME \\
    --connection-string "$CONNECTION_STRING" \\
    --public-access off \\
    --output table

# Configure backup retention policies
echo "Configuring lifecycle management policies..."
POLICY_JSON='{
  "rules": [
    {
      "name": "DeleteOldBackups",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["backup_"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 90
            },
            "delete": {
              "daysAfterModificationGreaterThan": 365
            }
          }
        }
      }
    }
  ]
}'

echo "$POLICY_JSON" | az storage account management-policy create \\
    --account-name $STORAGE_ACCOUNT \\
    --policy @-

# Set up monitoring and alerts
echo "Setting up monitoring alerts..."

# Create action group for notifications
az monitor action-group create \\
    --resource-group $RESOURCE_GROUP \\
    --name "backup-alerts" \\
    --short-name "backup" \\
    --output table

# Create alert for backup failures
az monitor metrics alert create \\
    --name "backup-failure-alert" \\
    --resource-group $RESOURCE_GROUP \\
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT" \\
    --condition "avg transactions < 1" \\
    --window-size 24h \\
    --evaluation-frequency 12h \\
    --action "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/microsoft.insights/actionGroups/backup-alerts" \\
    --description "Alert when no backup activity detected in 24 hours" \\
    --output table

# Output configuration
echo ""
echo "=== SETUP COMPLETE ==="
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Container: $CONTAINER_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""
echo "Add this to your environment variables:"
echo "export AZURE_STORAGE_CONNECTION_STRING='$CONNECTION_STRING'"
echo ""
echo "Or add to your Azure App Service configuration:"
echo "AZURE_STORAGE_CONNECTION_STRING = $CONNECTION_STRING"
echo ""

# Save configuration to file
cat > azure_backup_config.json << EOF
{
  "resource_group": "$RESOURCE_GROUP",
  "storage_account": "$STORAGE_ACCOUNT",
  "container_name": "$CONTAINER_NAME",
  "location": "$LOCATION",
  "connection_string": "$CONNECTION_STRING"
}
EOF

echo "Configuration saved to: azure_backup_config.json"
'''
    
    with open('setup_azure_backup.sh', 'w', encoding='utf-8') as f:
        f.write(script)
    
    # Make executable
    try:
        os.chmod('setup_azure_backup.sh', 0o755)
    except:
        pass
    
    print("✅ Created Azure setup script: setup_azure_backup.sh")

def create_backup_test_script():
    """Create comprehensive backup system test script"""
    # Create the script content as a string with proper escaping
    script_content = """#!/usr/bin/env python3
'''
Backup System Integration Test
=============================

Comprehensive test of backup and restore functionality
'''

import sys
import os
import tempfile
import shutil
import sqlite3
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from azure_backup_system import AzureBackupManager
from data_integrity_monitor import DataIntegrityMonitor

def create_test_database(db_path):
    '''Create a test database with sample data'''
    conn = sqlite3.connect(db_path)
    try:
        # Create users table
        users_sql = '''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        conn.execute(users_sql)
        
        # Create courses table
        courses_sql = '''
            CREATE TABLE courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        conn.execute(courses_sql)
        
        # Insert test data
        test_users = [
            ('testuser1', 'hash1', 'Beginner', 50),
            ('testuser2', 'hash2', 'Intermediate', 150),
            ('testuser3', 'hash3', 'Expert', 300)
        ]
        
        for username, password_hash, level, points in test_users:
            conn.execute(
                'INSERT INTO users (username, password_hash, level, points) VALUES (?, ?, ?, ?)',
                (username, password_hash, level, points)
            )
        
        test_courses = [
            ('Python Basics', 'Learn Python programming', 'Beginner'),
            ('Advanced Flask', 'Master Flask web development', 'Intermediate'),
            ('Machine Learning', 'Introduction to ML', 'Expert')
        ]
        
        for title, description, level in test_courses:
            conn.execute(
                'INSERT INTO courses (title, description, level) VALUES (?, ?, ?)',
                (title, description, level)
            )
        
        conn.commit()
        print(f"✅ Created test database with {len(test_users)} users and {len(test_courses)} courses")
        
    finally:
        conn.close()

def test_backup_restore_cycle():
    '''Test complete backup and restore cycle'''
    print("=== TESTING BACKUP AND RESTORE CYCLE ===")
    
    # Check for Azure connection string
    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not set")
        print("Run setup_azure_backup.sh first and set the environment variable")
        return False
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, 'test_ai_learning.db')
        
        try:
            # Step 1: Create test database
            print("\\\\n1. Creating test database...")
            create_test_database(test_db_path)
            
            # Step 2: Initialize backup manager
            print("\\\\n2. Initializing backup manager...")
            backup_manager = AzureBackupManager(
                connection_string=connection_string,
                container_name="ai-learning-backups-test",
                db_path=test_db_path
            )
            
            # Step 3: Create backup
            print("\\\\n3. Creating backup...")
            backup_metadata = backup_manager.create_backup("test")
            
            if not backup_metadata:
                print("❌ Backup creation failed")
                return False
            
            print(f"✅ Backup created: {backup_metadata.backup_id}")
            
            # Step 4: Modify database to simulate changes
            print("\\\\n4. Modifying database...")
            conn = sqlite3.connect(test_db_path)
            conn.execute("INSERT INTO users (username, password_hash) VALUES ('testuser4', 'hash4')")
            conn.execute("DELETE FROM courses WHERE id = 1")
            conn.commit()
            conn.close()
            
            # Step 5: Restore from backup
            print("\\\\n5. Restoring from backup...")
            restored_db_path = os.path.join(temp_dir, 'restored.db')
            
            success = backup_manager.restore_from_backup(backup_metadata.backup_id, restored_db_path)
            
            if not success:
                print("❌ Restore failed")
                return False
            
            print("✅ Restore completed")
            
            # Step 6: Verify restored data
            print("\\\\n6. Verifying restored data...")
            
            # Check original data is restored
            conn = sqlite3.connect(restored_db_path)
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
            conn.close()
            
            if user_count == 3 and course_count == 3:
                print(f"✅ Data verified: {user_count} users, {course_count} courses")
            else:
                print(f"❌ Data verification failed: {user_count} users, {course_count} courses")
                return False
            
            # Step 7: Test integrity monitoring
            print("\\\\n7. Testing integrity monitoring...")
            integrity_monitor = DataIntegrityMonitor(test_db_path)
            
            # Save snapshot
            if integrity_monitor.save_pre_deployment_snapshot():
                print("✅ Pre-deployment snapshot saved")
            else:
                print("❌ Failed to save snapshot")
                return False
            
            # Run post-deployment check
            report = integrity_monitor.run_post_deployment_check()
            if report.overall_result.value == "PASS":
                print("✅ Integrity check passed")
            else:
                print(f"❌ Integrity check failed: {report.overall_result.value}")
                return False
            
            print("\\\\n=== ALL TESTS PASSED ===")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False

def test_backup_health_monitoring():
    '''Test backup health monitoring'''
    print("\\\\n=== TESTING BACKUP HEALTH MONITORING ===")
    
    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not set")
        return False
    
    try:
        backup_manager = AzureBackupManager(connection_string, "ai-learning-backups-test")
        health = backup_manager.get_backup_health_status()
        
        print(f"Health Status: {health['status']}")
        print(f"Message: {health['message']}")
        print(f"Total Backups: {health['total_backups']}")
        
        if health['status'] in ['HEALTHY', 'WARNING']:
            print("✅ Health monitoring working")
            return True
        else:
            print("❌ Health monitoring issues detected")
            return False
            
    except Exception as e:
        print(f"❌ Health monitoring test failed: {e}")
        return False

def main():
    '''Run all tests'''
    print("AI Learning Tracker - Backup System Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Backup and restore cycle
    if test_backup_restore_cycle():
        tests_passed += 1
    
    # Test 2: Health monitoring
    if test_backup_health_monitoring():
        tests_passed += 1
    
    print(f"\\\\n=== TEST RESULTS ===")
    print(f"Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
    
    with open('test_backup_system.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    try:
        os.chmod('test_backup_system.py', 0o755)
    except:
        pass
    
    print("✅ Created backup test script: test_backup_system.py")

def create_deployment_pipeline_integration():
    """Create Azure DevOps/GitHub Actions integration scripts"""
    
    # GitHub Actions workflow
    github_workflow = '''name: Safe Deployment with Data Integrity

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  pre-deployment-checks:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install azure-storage-blob
    
    - name: Run Pre-Deployment Checks
      env:
        AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
      run: |
        python -c "from deployment_safety import deployment_safety; deployment_safety.create_pre_deployment_backup()"
        python data_integrity_monitor.py pre
    
    - name: Run Tests
      run: |
        python -m pytest tests/ -v
    
  deploy:
    needs: pre-deployment-checks
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/master'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Azure App Service
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'ai-learning-tracker-bharath'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
    
    - name: Post-Deployment Integrity Check
      env:
        AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
      run: |
        sleep 30  # Wait for deployment to complete
        python data_integrity_monitor.py post
    
    - name: Notify on Failure
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        text: '🚨 Deployment failed - Data integrity issues detected!'
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
'''
    
    os.makedirs('.github/workflows', exist_ok=True)
    with open('.github/workflows/safe-deployment.yml', 'w', encoding='utf-8') as f:
        f.write(github_workflow)
    
    # Azure DevOps pipeline
    azure_pipeline = '''trigger:
- master

pool:
  vmImage: ubuntu-latest

variables:
  azureServiceConnection: 'azure-service-connection'
  webAppName: 'ai-learning-tracker-bharath'

stages:
- stage: PreDeployment
  displayName: 'Pre-Deployment Safety Checks'
  jobs:
  - job: SafetyChecks
    displayName: 'Run Safety Checks'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.9'
    
    - script: |
        pip install -r requirements.txt
        pip install azure-storage-blob
      displayName: 'Install dependencies'
    
    - script: |
        python data_integrity_monitor.py pre
      env:
        AZURE_STORAGE_CONNECTION_STRING: $(AzureStorageConnectionString)
      displayName: 'Pre-deployment integrity check'
    
    - script: |
        python -c "from deployment_safety import deployment_safety; deployment_safety.create_pre_deployment_backup()"
      env:
        AZURE_STORAGE_CONNECTION_STRING: $(AzureStorageConnectionString)
      displayName: 'Create pre-deployment backup'

- stage: Deploy
  displayName: 'Deploy to Azure'
  dependsOn: PreDeployment
  condition: succeeded()
  jobs:
  - deployment: DeployWeb
    displayName: 'Deploy to Azure App Service'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebApp@1
            inputs:
              azureSubscription: $(azureServiceConnection)
              appType: 'webAppLinux'
              appName: $(webAppName)
              package: '$(Pipeline.Workspace)/drop'

- stage: PostDeployment
  displayName: 'Post-Deployment Validation'
  dependsOn: Deploy
  condition: succeeded()
  jobs:
  - job: ValidationChecks
    displayName: 'Run Validation Checks'
    steps:
    - script: |
        sleep 30  # Wait for deployment
        python data_integrity_monitor.py post
      env:
        AZURE_STORAGE_CONNECTION_STRING: $(AzureStorageConnectionString)
      displayName: 'Post-deployment integrity check'
    
    - script: |
        if [ $? -ne 0 ]; then
          echo "##vso[task.logissue type=error]Data integrity check failed!"
          exit 1
        fi
      displayName: 'Validate integrity check results'
'''
    
    with open('azure-pipelines.yml', 'w', encoding='utf-8') as f:
        f.write(azure_pipeline)
    
    print("✅ Created deployment pipeline configurations")

if __name__ == "__main__":
    print("Creating Azure backup and disaster recovery system...")
    
    create_azure_resources_script()
    create_backup_test_script()
    create_deployment_pipeline_integration()
    
    print("\\n=== SETUP COMPLETE ===")
    print("\\nNext steps:")
    print("1. Run: ./setup_azure_backup.sh")
    print("2. Set environment variable: AZURE_STORAGE_CONNECTION_STRING")
    print("3. Test system: python test_backup_system.py")
    print("4. Integrate with your Flask app using deployment_safety.py")
    print("\\n🛡️ Your application now has enterprise-grade data protection!")
