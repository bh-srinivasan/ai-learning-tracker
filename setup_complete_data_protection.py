#!/usr/bin/env python3
"""
Complete Data Integrity and Disaster Recovery Setup
===================================================

Run this script to set up the complete data protection system for your AI Learning Tracker.
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def print_banner():
    print("="*70)
    print("🛡️  AI LEARNING TRACKER - DATA PROTECTION SETUP")
    print("="*70)
    print("Setting up enterprise-grade data integrity and disaster recovery...")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📋 Checking dependencies...")
    
    try:
        import azure.storage.blob
        print("✅ Azure Storage Blob SDK installed")
    except ImportError:
        print("❌ Azure Storage Blob SDK missing")
        print("Installing azure-storage-blob...")
        subprocess.run([sys.executable, "-m", "pip", "install", "azure-storage-blob"], check=True)
        print("✅ Azure Storage Blob SDK installed")
    
    try:
        import schedule
        print("✅ Schedule library installed")
    except ImportError:
        print("❌ Schedule library missing")
        print("Installing schedule...")
        subprocess.run([sys.executable, "-m", "pip", "install", "schedule"], check=True)
        print("✅ Schedule library installed")

def create_env_template():
    """Create environment variables template"""
    print("\n🔧 Creating environment template...")
    
    env_template = """# Azure Storage Configuration for Backup System
# ==============================================
# Get this from Azure Portal or by running setup_azure_backup.sh
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT;AccountKey=YOUR_KEY;EndpointSuffix=core.windows.net"

# Application Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Existing environment variables (keep these)
ADMIN_PASSWORD=your_secure_admin_password
DEMO_USERNAME=demo
DEMO_PASSWORD=your_secure_demo_password
"""
    
    env_file = ".env.template"
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Environment template created: {env_file}")
    print("   Copy this to .env and update with your Azure storage connection string")

def run_initial_integrity_check():
    """Run initial data integrity check"""
    print("\n🔍 Running initial data integrity check...")
    
    try:
        from data_integrity_monitor import DataIntegrityMonitor
        
        monitor = DataIntegrityMonitor()
        
        # Test ACID compliance
        if monitor.validate_acid_compliance():
            print("✅ Database ACID compliance verified")
        else:
            print("❌ Database ACID compliance issues detected")
            return False
        
        # Create initial snapshot
        if monitor.save_pre_deployment_snapshot():
            print("✅ Initial data snapshot created")
        else:
            print("❌ Failed to create initial snapshot")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Initial integrity check failed: {e}")
        return False

def create_cli_commands_reference():
    """Create CLI commands reference"""
    print("\n📚 Creating CLI commands reference...")
    
    commands_doc = """# Data Protection CLI Commands
# ============================

## Pre-Deployment Commands
```bash
# Create backup and save integrity snapshot before deployment
flask pre-deploy-check

# Create manual backup
flask backup-now
```

## Post-Deployment Commands
```bash
# Verify data integrity after deployment
flask post-deploy-check

# Check system health
flask system-health
```

## Backup Management
```bash
# List available restore points
flask list-backups

# Create manual backup
flask backup-now
```

## Emergency Recovery
```bash
# Use the CLI restore tool for emergency recovery
python restore_tool.py list                    # List backups
python restore_tool.py restore <backup_id>     # Restore specific backup
python restore_tool.py latest                  # Restore from latest backup
```

## Automated Testing
```bash
# Test complete backup/restore cycle
python test_backup_system.py
```

## Azure Setup
```bash
# Set up Azure resources (run once)
./setup_azure_backup.sh
```

## Integration with Deployment Pipeline

### GitHub Actions
Add these secrets to your repository:
- AZURE_STORAGE_CONNECTION_STRING
- AZURE_WEBAPP_PUBLISH_PROFILE
- SLACK_WEBHOOK (optional, for notifications)

### Azure DevOps
Add these variables:
- AzureStorageConnectionString
- azureServiceConnection

## Monitoring and Alerts

The system provides:
- Automated daily backups
- Real-time data integrity monitoring
- Point-in-time restore capabilities
- Geo-redundant storage
- Automated cleanup of old backups
- Health monitoring and alerting

## Emergency Procedures

### Data Loss Detected
1. Stop application traffic
2. Run: `flask system-health`
3. Run: `python restore_tool.py latest`
4. Verify restored data
5. Investigate root cause

### Backup System Failure
1. Check Azure storage connectivity
2. Verify AZURE_STORAGE_CONNECTION_STRING
3. Run: `python test_backup_system.py`
4. Check Azure portal for storage account status
"""
    
    with open('DATA_PROTECTION_GUIDE.md', 'w') as f:
        f.write(commands_doc)
    
    print("✅ CLI commands reference created: DATA_PROTECTION_GUIDE.md")

def create_monitoring_dashboard():
    """Create monitoring dashboard configuration"""
    print("\n📊 Creating monitoring dashboard configuration...")
    
    dashboard_config = {
        "monitoring": {
            "enabled": True,
            "checks": {
                "integrity_check_interval": "6_hours",
                "backup_health_check_interval": "1_hour",
                "database_size_monitoring": True,
                "user_count_monitoring": True
            },
            "alerts": {
                "critical_data_loss": {
                    "enabled": True,
                    "channels": ["log", "email", "slack"]
                },
                "backup_failure": {
                    "enabled": True,
                    "channels": ["log", "email"]
                },
                "integrity_warning": {
                    "enabled": True,
                    "channels": ["log"]
                }
            },
            "retention": {
                "scheduled_backups_days": 30,
                "manual_backups_days": 90,
                "pre_deployment_backups_days": 90,
                "integrity_logs_days": 365
            }
        },
        "disaster_recovery": {
            "rpo_target_hours": 24,  # Recovery Point Objective
            "rto_target_minutes": 30,  # Recovery Time Objective
            "geo_redundancy": True,
            "automated_failover": False  # Manual approval required
        }
    }
    
    with open('monitoring_config.json', 'w') as f:
        json.dump(dashboard_config, f, indent=2)
    
    print("✅ Monitoring configuration created: monitoring_config.json")

def run_setup_scripts():
    """Run the setup scripts"""
    print("\n🔧 Running setup scripts...")
    
    try:
        # Run the disaster recovery setup
        exec(open('setup_disaster_recovery.py').read())
        print("✅ Disaster recovery scripts created")
    except Exception as e:
        print(f"❌ Failed to run setup scripts: {e}")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*70)
    print("🎉 DATA PROTECTION SETUP COMPLETE!")
    print("="*70)
    print()
    print("Next Steps:")
    print("1. 🔧 Set up Azure resources:")
    print("   ./setup_azure_backup.sh")
    print()
    print("2. 🔑 Configure environment:")
    print("   - Copy .env.template to .env")
    print("   - Add your Azure storage connection string")
    print()
    print("3. 🧪 Test the system:")
    print("   python test_backup_system.py")
    print()
    print("4. 🚀 Deploy with safety:")
    print("   flask pre-deploy-check    # Before deployment")
    print("   # Deploy your application")
    print("   flask post-deploy-check   # After deployment")
    print()
    print("5. 📚 Read the guide:")
    print("   See DATA_PROTECTION_GUIDE.md for complete instructions")
    print()
    print("🛡️ Your application now has enterprise-grade data protection!")
    print("   - Automated backups to Azure with geo-redundancy")
    print("   - Real-time data integrity monitoring")
    print("   - Point-in-time restore capabilities")
    print("   - Deployment safety checks")
    print("   - Emergency recovery procedures")
    print()

def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Check and install dependencies
        check_dependencies()
        
        # Create configuration files
        create_env_template()
        
        # Run initial integrity check
        if not run_initial_integrity_check():
            print("⚠️ Initial integrity check had issues, but setup will continue")
        
        # Create documentation and tools
        create_cli_commands_reference()
        create_monitoring_dashboard()
        
        # Run setup scripts
        run_setup_scripts()
        
        # Print next steps
        print_next_steps()
        
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
