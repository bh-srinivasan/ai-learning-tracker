"""
Azure Backup Investigation Script
Checks what backup and recovery options might be available for the Azure App Service
"""

import subprocess
import json
from datetime import datetime

def run_azure_command(command):
    """Run Azure CLI command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return None, str(e), 1

def check_azure_app_service_backups():
    """Check if there are any backups available for the app service"""
    print("🔍 Checking Azure App Service backup options...")
    
    # List app service plans and backups
    commands = [
        "az account show",
        "az webapp list --query '[].{name:name, resourceGroup:resourceGroup}'",
        # Note: The actual backup commands would depend on the specific setup
    ]
    
    results = []
    for cmd in commands:
        print(f"\n📋 Running: {cmd}")
        stdout, stderr, code = run_azure_command(cmd)
        
        if code == 0:
            print("✅ Success:")
            print(stdout[:500] + "..." if len(stdout) > 500 else stdout)
        else:
            print("❌ Error:")
            print(stderr)
        
        results.append({
            'command': cmd,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': code,
            'timestamp': datetime.now().isoformat()
        })
    
    return results

def check_git_history_for_production_data():
    """Check git history to see if production data was ever committed"""
    print("\n🔍 Checking git history for production data...")
    
    git_commands = [
        "git log --oneline -10",
        "git log --grep='ai_learning.db' --oneline",
        "git log --name-only --oneline -5",
    ]
    
    for cmd in git_commands:
        print(f"\n📋 Running: {cmd}")
        stdout, stderr, code = run_azure_command(cmd)
        
        if code == 0:
            print("✅ Git History:")
            print(stdout)
        else:
            print("❌ Git Error:")
            print(stderr)

def generate_recovery_investigation_report():
    """Generate a comprehensive report for recovery options"""
    
    report = f"""
# AZURE RECOVERY INVESTIGATION REPORT

**Generated**: {datetime.now().isoformat()}
**Purpose**: Investigate options to recover production data overwritten by local data

## Summary of the Breach
- Local development database was copied to Azure production
- Real user data was overwritten with test data
- This happened when forcing ai_learning.db into git and pushing to Azure

## Recovery Options to Investigate

### 1. Azure App Service Backup Features
- **File System Backups**: Check if automatic backups are enabled
- **Database Backups**: SQLite file might be included in file system backups
- **Slot Deployments**: Check if production slot has backup configurations

### 2. Azure Infrastructure Backups
- **Resource Group Backups**: Check if resource group has backup policies
- **Storage Account Backups**: If SQLite file is stored separately
- **Deployment History**: Check deployment history for rollback options

### 3. Git Repository Recovery
- **Commit History**: Check if production data was ever committed to git
- **Branch Analysis**: Look for branches that might contain production state
- **Remote Tracking**: Check if Azure remote has different history

### 4. Azure Support Options
- **Submit Support Ticket**: Request emergency data recovery assistance
- **Point-in-Time Recovery**: Check if available for App Service files
- **Backup Restoration**: Professional assistance with data recovery

## Immediate Actions Required

1. **Do NOT make any more changes to Azure**
2. **Contact Azure Support immediately**
3. **Document exact time of data overwrite**
4. **Preserve current state for investigation**

## Azure Support Contact Information
- Submit ticket through Azure Portal
- Explain: "Critical data loss - production database overwritten"
- Request: Emergency data recovery assistance
- Urgency: Critical/Severe

## Prevention for Future
- Implement proper backup strategy
- Never allow local data to reach production
- Use staging environments for testing
- Implement database migration controls
"""
    
    return report

if __name__ == "__main__":
    print("🚨 AZURE RECOVERY INVESTIGATION 🚨")
    print("=" * 50)
    
    # Check Azure backups
    backup_results = check_azure_app_service_backups()
    
    # Check git history
    check_git_history_for_production_data()
    
    # Generate recovery report
    recovery_report = generate_recovery_investigation_report()
    
    # Save results
    with open('azure_recovery_investigation.json', 'w') as f:
        json.dump({
            'backup_investigation': backup_results,
            'recovery_report': recovery_report,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print("\n📄 Full recovery report:")
    print(recovery_report)
    
    print("\n🚨 NEXT STEPS:")
    print("1. Contact Azure Support IMMEDIATELY")
    print("2. Do NOT make any more changes to Azure")
    print("3. Preserve all evidence of the breach")
    print("4. Wait for professional recovery assistance")
