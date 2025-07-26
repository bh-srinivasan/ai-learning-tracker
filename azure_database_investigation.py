"""
Azure Database Investigation
============================
Check why Azure database became empty (0 users, 0 courses)
DO NOT touch local database - focus ONLY on Azure
"""

import os
import json
from datetime import datetime

def investigate_azure_database_loss():
    """Investigate what caused Azure database to become empty"""
    
    print("🔍 AZURE DATABASE INVESTIGATION")
    print("===============================")
    print("⚠️  Issue: Azure database has 0 users and 0 courses")
    print("🎯 Goal: Find root cause and recovery options")
    print()
    
    # Check for Azure configuration issues
    print("1. CHECKING AZURE CONFIGURATION...")
    
    # Look for Azure environment variables or config
    azure_configs = []
    
    # Check common Azure environment variables
    azure_vars = [
        'AZURE_STORAGE_CONNECTION_STRING',
        'AZURE_STORAGE_ACCOUNT_NAME', 
        'AZURE_STORAGE_ACCOUNT_KEY',
        'DATABASE_URL',
        'AZURE_SQL_CONNECTION_STRING',
        'SQLCONNSTR_DefaultConnection'
    ]
    
    for var in azure_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive info
            masked = value[:20] + "..." if len(value) > 20 else value
            azure_configs.append(f"  ✅ {var}: {masked}")
        else:
            azure_configs.append(f"  ❌ {var}: Not set")
    
    if azure_configs:
        print("   Azure Environment Variables:")
        for config in azure_configs:
            print(config)
    else:
        print("   ❌ No Azure environment variables found")
    
    print()
    
    # Check for Azure deployment artifacts
    print("2. CHECKING DEPLOYMENT ARTIFACTS...")
    
    deployment_files = [
        'azure-pipelines.yml',
        'deploy_azure_secure.py',
        'azure_deployment_security_audit.py',
        'azure_database_sync.py'
    ]
    
    found_files = []
    for file in deployment_files:
        if os.path.exists(file):
            found_files.append(f"  ✅ {file}")
        else:
            found_files.append(f"  ❌ {file}: Missing")
    
    for file_status in found_files:
        print(file_status)
    
    print()
    
    # Check for recent deployment logs
    print("3. CHECKING FOR DEPLOYMENT LOGS...")
    
    log_patterns = [
        'azure_db_init.log',
        'backup_system.log', 
        'data_integrity.log',
        'azure-logs-latest.zip'
    ]
    
    for log_file in log_patterns:
        if os.path.exists(log_file):
            print(f"  ✅ Found: {log_file}")
            try:
                # Read last few lines of log
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"      Last entry: {lines[-1].strip()}")
            except Exception as e:
                print(f"      Error reading: {e}")
        else:
            print(f"  ❌ Missing: {log_file}")
    
    print()
    
    # Analyze potential causes
    print("4. POTENTIAL CAUSES ANALYSIS...")
    print("  📋 Possible reasons for empty Azure database:")
    print("     1. Fresh deployment overwrote existing database")
    print("     2. Database connection string changed")
    print("     3. New Azure SQL database was created")
    print("     4. Migration script ran but failed to preserve data")
    print("     5. Azure Storage sync is not working")
    print("     6. Environment variables pointing to wrong database")
    
    print()
    
    # Recovery recommendations
    print("5. RECOVERY RECOMMENDATIONS...")
    print("  🔧 Immediate actions needed:")
    print("     1. Check Azure portal for database status")
    print("     2. Verify connection strings in Azure App Service")
    print("     3. Check if backups exist in Azure Storage")
    print("     4. Look for database migration logs")
    print("     5. Check if Azure SQL database was recreated")
    
    print()
    
    # Create investigation report
    report = {
        "timestamp": datetime.now().isoformat(),
        "issue": "Azure database empty (0 users, 0 courses)",
        "investigation_completed": True,
        "azure_configs_found": len([c for c in azure_configs if "✅" in c]),
        "deployment_files_found": len([f for f in found_files if "✅" in f]),
        "next_steps": [
            "Check Azure Portal database status",
            "Verify App Service connection strings", 
            "Look for Azure Storage backups",
            "Check deployment logs in Azure"
        ]
    }
    
    with open('azure_investigation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("📊 Investigation report saved: azure_investigation_report.json")
    print()
    print("🚨 NEXT STEPS:")
    print("   1. Check Azure Portal for your database status")
    print("   2. Verify connection strings in Azure App Service settings")
    print("   3. Look for any Azure Storage backups")
    print("   4. Check Azure deployment logs")

if __name__ == "__main__":
    investigate_azure_database_loss()
