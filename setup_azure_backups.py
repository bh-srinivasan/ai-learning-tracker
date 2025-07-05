#!/usr/bin/env python3
"""
Azure Backup Management Script
Configures and manages Azure backups for the AI Learning application
"""

import subprocess
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

class AzureBackupSetup:
    """Manages Azure backup configuration and operations"""
    
    def __init__(self):
        self.resource_group = "ai-learning-rg"
        self.webapp_name = "ai-learning-tracker-bharath"
        self.backup_resource_group = "ai-learning-backup-rg"
        self.storage_account = "ailearningbackups2025"
        self.container_name = "webapp-backups"
        self.location = "Central US"
        
    def run_az_command(self, command: List[str]) -> Dict:
        """Run Azure CLI command and return result"""
        
        try:
            # Use full path to az command if needed
            result = subprocess.run(
                ['az'] + command,
                capture_output=True,
                text=True,
                check=False,
                shell=True  # Add shell=True for Windows
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def check_azure_login(self) -> bool:
        """Check if user is logged into Azure CLI"""
        
        print("🔍 Checking Azure CLI login status...")
        result = self.run_az_command(['account', 'show'])
        
        if result['success']:
            account_info = json.loads(result['stdout'])
            print(f"✅ Logged in as: {account_info.get('user', {}).get('name', 'Unknown')}")
            print(f"   Subscription: {account_info.get('name', 'Unknown')}")
            return True
        else:
            print("❌ Not logged into Azure CLI")
            print("   Run: az login")
            return False
    
    def create_backup_storage_account(self) -> bool:
        """Create storage account for backups"""
        
        print(f"📦 Creating backup storage account: {self.storage_account}")
        
        # Create resource group for backups
        print(f"   Creating resource group: {self.backup_resource_group}")
        result = self.run_az_command([
            'group', 'create',
            '--name', self.backup_resource_group,
            '--location', self.location
        ])
        
        if not result['success'] and 'already exists' not in result['stderr']:
            print(f"❌ Failed to create resource group: {result['stderr']}")
            return False
        
        # Create storage account
        print(f"   Creating storage account: {self.storage_account}")
        result = self.run_az_command([
            'storage', 'account', 'create',
            '--name', self.storage_account,
            '--resource-group', self.backup_resource_group,
            '--location', self.location,
            '--sku', 'Standard_LRS',
            '--kind', 'StorageV2'
        ])
        
        if not result['success']:
            if 'already exists' in result['stderr']:
                print(f"✅ Storage account already exists")
            else:
                print(f"❌ Failed to create storage account: {result['stderr']}")
                return False
        else:
            print(f"✅ Storage account created successfully")
        
        # Create container
        print(f"   Creating container: {self.container_name}")
        result = self.run_az_command([
            'storage', 'container', 'create',
            '--name', self.container_name,
            '--account-name', self.storage_account
        ])
        
        if not result['success'] and 'already exists' not in result['stderr']:
            print(f"❌ Failed to create container: {result['stderr']}")
            return False
        
        print(f"✅ Backup storage setup completed")
        return True
    
    def configure_automated_backup(self) -> bool:
        """Configure automated backup for the webapp"""
        
        print("⚙️ Configuring automated webapp backup...")
        
        # Get storage account key
        result = self.run_az_command([
            'storage', 'account', 'keys', 'list',
            '--account-name', self.storage_account,
            '--resource-group', self.backup_resource_group
        ])
        
        if not result['success']:
            print(f"❌ Failed to get storage account key: {result['stderr']}")
            return False
        
        keys = json.loads(result['stdout'])
        if not keys:
            print("❌ No storage account keys found")
            return False
        
        storage_key = keys[0]['value']
        
        # Create backup configuration
        container_url = f"https://{self.storage_account}.blob.core.windows.net/{self.container_name}"
        
        # Note: Real backup configuration requires SAS token or connection string
        print(f"   Container URL: {container_url}")
        print(f"   Backup frequency: Daily")
        print(f"   Retention period: 30 days")
        
        # For demonstration, show the command that would be used
        backup_command = [
            'webapp', 'config', 'backup', 'create',
            '--resource-group', self.resource_group,
            '--webapp-name', self.webapp_name,
            '--container-url', container_url,
            '--frequency', '1440',  # Daily in minutes
            '--retention', '30',    # 30 days
            '--backup-name', 'ai-learning-daily-backup'
        ]
        
        print("⚠️ Backup configuration command (requires proper SAS token):")
        print(f"   az {' '.join(backup_command)}")
        
        # In a real implementation, you would need to:
        # 1. Generate a SAS token for the container
        # 2. Use the SAS token in the container URL
        # 3. Execute the backup configuration command
        
        return True
    
    def check_backup_status(self) -> Dict:
        """Check current backup status"""
        
        print("🔍 Checking current backup status...")
        
        result = self.run_az_command([
            'webapp', 'config', 'backup', 'list',
            '--resource-group', self.resource_group,
            '--webapp-name', self.webapp_name
        ])
        
        if result['success']:
            backups = json.loads(result['stdout']) if result['stdout'] else []
            
            status = {
                'configured': len(backups) > 0,
                'backup_count': len(backups),
                'backups': backups
            }
            
            if status['configured']:
                print(f"✅ Backups configured: {status['backup_count']} backup configuration(s)")
                for i, backup in enumerate(backups, 1):
                    print(f"   {i}. Name: {backup.get('name', 'Unknown')}")
                    print(f"      Status: {backup.get('backupStatus', 'Unknown')}")
                    print(f"      Created: {backup.get('created', 'Unknown')}")
            else:
                print("⚠️ No backups configured")
            
            return status
        else:
            print(f"❌ Failed to check backup status: {result['stderr']}")
            return {'configured': False, 'error': result['stderr']}
    
    def create_manual_backup(self, backup_name: Optional[str] = None) -> bool:
        """Create a manual backup"""
        
        if not backup_name:
            backup_name = f"manual-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        print(f"💾 Creating manual backup: {backup_name}")
        
        result = self.run_az_command([
            'webapp', 'config', 'backup', 'create',
            '--resource-group', self.resource_group,
            '--webapp-name', self.webapp_name,
            '--backup-name', backup_name
        ])
        
        if result['success']:
            print(f"✅ Manual backup '{backup_name}' created successfully")
            return True
        else:
            print(f"❌ Failed to create manual backup: {result['stderr']}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Set up backup monitoring and alerts"""
        
        print("📊 Setting up backup monitoring...")
        
        # This would typically involve:
        # 1. Creating Azure Monitor alerts for backup failures
        # 2. Setting up Log Analytics workspace
        # 3. Configuring notification groups
        
        monitoring_queries = [
            "# Monitor backup status",
            "AzureDiagnostics",
            "| where ResourceProvider == 'MICROSOFT.WEB'",
            "| where Category == 'AppServiceHTTPLogs'",
            "| where RequestUri_s contains 'backup'",
            "| order by TimeGenerated desc"
        ]
        
        print("   Backup monitoring queries:")
        for query in monitoring_queries:
            print(f"     {query}")
        
        print("✅ Monitoring setup instructions created")
        return True

def main():
    """Main setup function"""
    
    print("🔧 AZURE BACKUP CONFIGURATION SETUP")
    print("=" * 50)
    
    setup = AzureBackupSetup()
    
    # Check Azure login
    if not setup.check_azure_login():
        print("\n❌ Setup aborted: Please login to Azure CLI first")
        print("   Run: az login")
        return False
    
    # Create backup storage
    print(f"\n📦 Setting up backup storage...")
    if not setup.create_backup_storage_account():
        print("❌ Failed to set up backup storage")
        return False
    
    # Check current backup status
    print(f"\n🔍 Checking current backup configuration...")
    backup_status = setup.check_backup_status()
    
    # Configure automated backups
    if not backup_status.get('configured', False):
        print(f"\n⚙️ Configuring automated backups...")
        setup.configure_automated_backup()
    else:
        print(f"\n✅ Automated backups already configured")
    
    # Set up monitoring
    print(f"\n📊 Setting up monitoring...")
    setup.setup_monitoring()
    
    # Generate summary
    print(f"\n" + "=" * 50)
    print("🎯 BACKUP SETUP SUMMARY")
    print(f"✅ Storage Account: {setup.storage_account}")
    print(f"✅ Container: {setup.container_name}")
    print(f"✅ Resource Group: {setup.backup_resource_group}")
    print(f"⚠️ Manual backup configuration may be required")
    print(f"📋 Next steps:")
    print(f"   1. Verify backup configuration in Azure Portal")
    print(f"   2. Test backup creation and restoration")
    print(f"   3. Set up monitoring alerts")
    print(f"   4. Document backup procedures")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Azure backup setup completed successfully")
        else:
            print("\n❌ Azure backup setup failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
