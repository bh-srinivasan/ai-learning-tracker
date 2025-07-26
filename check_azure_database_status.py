"""
Azure Database Status Checker
=============================
Check the actual status of Azure database - what went wrong and how to fix it
"""

import requests
import json
import os
from datetime import datetime

def check_azure_database_status():
    """Check Azure database status and provide specific recovery steps"""
    
    print("🔍 AZURE DATABASE STATUS CHECK")
    print("===============================")
    print("🎯 Checking why Azure database became empty")
    print()
    
    # First, let's check what your Azure configuration should be
    print("1. EXPECTED AZURE CONFIGURATION...")
    
    expected_configs = {
        "Azure App Service": "ai-learning-tracker",
        "Resource Group": "ai-learning-rg", 
        "Database Type": "SQLite with Azure Storage sync",
        "Storage Container": "database-backups",
        "Blob Name": "ai_learning.db"
    }
    
    for key, value in expected_configs.items():
        print(f"   {key}: {value}")
    
    print()
    
    # Check what went wrong during deployment
    print("2. DEPLOYMENT ISSUE ANALYSIS...")
    
    # Check if azure_database_sync.py has proper configuration
    if os.path.exists('azure_database_sync.py'):
        print("   ✅ Azure sync module exists")
        
        # Read the file to check configuration
        with open('azure_database_sync.py', 'r') as f:
            content = f.read()
            
        if 'AZURE_STORAGE_CONNECTION_STRING' in content:
            print("   ✅ Azure Storage connection string check found")
        else:
            print("   ❌ Azure Storage connection string check missing")
            
        if 'sync_from_azure_on_startup' in content:
            print("   ✅ Startup sync function exists")
        else:
            print("   ❌ Startup sync function missing")
    else:
        print("   ❌ Azure sync module missing")
    
    print()
    
    # Check main app integration
    print("3. APP INTEGRATION CHECK...")
    
    if os.path.exists('app.py'):
        with open('app.py', 'r') as f:
            app_content = f.read()
            
        if 'azure_database_sync' in app_content:
            print("   ✅ Azure sync imported in main app")
        else:
            print("   ❌ Azure sync NOT imported in main app")
            print("       🚨 THIS IS LIKELY THE PROBLEM!")
        
        if 'sync_from_azure_on_startup' in app_content:
            print("   ✅ Startup sync called in main app")
        else:
            print("   ❌ Startup sync NOT called in main app")
            print("       🚨 THIS IS LIKELY THE PROBLEM!")
    
    print()
    
    # Provide specific recovery steps
    print("4. RECOVERY STEPS FOR AZURE...")
    print("   🔧 To fix your empty Azure database:")
    print()
    print("   STEP 1: Check Azure App Service Settings")
    print("   - Go to Azure Portal → App Services → ai-learning-tracker")
    print("   - Go to Configuration → Application Settings")
    print("   - Check if AZURE_STORAGE_CONNECTION_STRING is set")
    print()
    print("   STEP 2: Check Azure Storage Account")
    print("   - Go to Storage Account in Azure Portal")
    print("   - Check if 'database-backups' container exists")
    print("   - Check if 'ai_learning.db' blob exists in container")
    print()
    print("   STEP 3: Verify App Startup Integration")
    print("   - Ensure azure_database_sync is called on app startup")
    print("   - Check Azure App Service logs for sync errors")
    print()
    print("   STEP 4: Manual Database Recovery Options")
    print("   a) If Azure Storage backup exists:")
    print("      - App should auto-download on next restart")
    print("   b) If no Azure Storage backup:")
    print("      - You'll need to recreate users/courses in Azure")
    print("      - Or manually upload a backup to Azure Storage")
    print()
    
    # Create specific Azure commands to check
    print("5. AZURE CLI COMMANDS TO RUN...")
    print("   Run these commands to check your Azure setup:")
    print()
    print("   # Check app service")
    print("   az webapp show --resource-group ai-learning-rg --name ai-learning-tracker")
    print()
    print("   # Check app settings")
    print("   az webapp config appsettings list --resource-group ai-learning-rg --name ai-learning-tracker")
    print()
    print("   # Check storage account")
    print("   az storage container list --account-name [your-storage-account]")
    print()
    print("   # Check for database backup in storage")
    print("   az storage blob list --container-name database-backups --account-name [your-storage-account]")
    print()
    
    # Save recovery instructions
    recovery_plan = {
        "timestamp": datetime.now().isoformat(),
        "issue": "Azure database empty - 0 users, 0 courses",
        "likely_cause": "Azure Storage sync not configured or failed",
        "immediate_actions": [
            "Check Azure Portal for storage connection string",
            "Verify database-backups container exists",
            "Check app.py has azure sync integration",
            "Review Azure App Service logs"
        ],
        "recovery_options": [
            "Restore from Azure Storage backup (if exists)",
            "Manually recreate data in Azure environment",
            "Upload local backup to Azure Storage (if authorized)"
        ]
    }
    
    with open('azure_recovery_plan.json', 'w') as f:
        json.dump(recovery_plan, f, indent=2)
    
    print(f"📋 Recovery plan saved: azure_recovery_plan.json")
    print()
    print("🚨 CRITICAL NEXT STEP:")
    print("   Check your Azure Portal to see if Azure Storage has a backup!")

if __name__ == "__main__":
    check_azure_database_status()
