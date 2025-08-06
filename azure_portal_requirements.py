#!/usr/bin/env python3
"""
Azure Portal Environment Variables Checker
Simulates what environment variables should be configured in Azure Portal Application Settings
"""

import os
from typing import Dict, List

def check_azure_portal_requirements():
    """
    Check what environment variables should be configured in Azure Portal
    for the AI Learning Tracker application
    """
    
    print(f"\n🌐 AZURE PORTAL APPLICATION SETTINGS REQUIREMENTS")
    print(f"{'='*80}")
    print(f"Location: Azure Portal > App Service > Configuration > Application Settings")
    
    # Required variables for Azure environment
    azure_required = {
        'SECRET_KEY': {
            'value': 'your-production-secret-key-change-this',
            'description': 'Flask session secret key - MUST be different from local!',
            'security_level': 'CRITICAL'
        },
        'ADMIN_PASSWORD': {
            'value': 'YourSecureAdminPasswordForProduction123!',
            'description': 'Admin user password for production environment',
            'security_level': 'CRITICAL'
        },
        'AZURE_SQL_SERVER': {
            'value': 'your-server-name.database.windows.net',
            'description': 'Azure SQL Server hostname',
            'security_level': 'HIGH'
        },
        'AZURE_SQL_DATABASE': {
            'value': 'ai-learning-tracker',
            'description': 'Azure SQL Database name',
            'security_level': 'HIGH'
        },
        'AZURE_SQL_USERNAME': {
            'value': 'sqladmin',
            'description': 'Azure SQL Database username',
            'security_level': 'HIGH'
        },
        'AZURE_SQL_PASSWORD': {
            'value': 'YourSecureSQLPassword123!',
            'description': 'Azure SQL Database password',
            'security_level': 'CRITICAL'
        }
    }
    
    # Optional variables for Azure environment
    azure_optional = {
        'FLASK_ENV': {
            'value': 'production',
            'description': 'Flask environment mode'
        },
        'FLASK_DEBUG': {
            'value': 'False',
            'description': 'Flask debug mode (should be False in production)'
        },
        'DEMO_PASSWORD': {
            'value': 'DemoUserPasswordForProduction123!',
            'description': 'Demo user password for testing in production'
        },
        'AZURE_STORAGE_CONNECTION_STRING': {
            'value': 'DefaultEndpointsProtocol=https;AccountName=...',
            'description': 'Azure Storage connection for backup system'
        }
    }
    
    print(f"\n🚨 REQUIRED APPLICATION SETTINGS (Must be configured):")
    print(f"{'Name':<30} | {'Example Value':<40} | {'Security':<8} | {'Description'}")
    print(f"{'-'*30} | {'-'*40} | {'-'*8} | {'-'*30}")
    
    for name, config in azure_required.items():
        example_value = config['value'][:35] + '...' if len(config['value']) > 35 else config['value']
        print(f"{name:<30} | {example_value:<40} | {config['security_level']:<8} | {config['description']}")
    
    print(f"\n⚙️ OPTIONAL APPLICATION SETTINGS:")
    print(f"{'Name':<30} | {'Example Value':<40} | {'Description'}")
    print(f"{'-'*30} | {'-'*40} | {'-'*30}")
    
    for name, config in azure_optional.items():
        example_value = config['value'][:35] + '...' if len(config['value']) > 35 else config['value']
        print(f"{name:<30} | {example_value:<40} | {config['description']}")
    
    print(f"\n📋 AZURE PORTAL CONFIGURATION STEPS:")
    print(f"{'='*80}")
    print(f"1. Open Azure Portal (https://portal.azure.com)")
    print(f"2. Navigate to your App Service resource")
    print(f"3. In the left sidebar, click 'Configuration'")
    print(f"4. Click 'Application settings' tab")
    print(f"5. For each required variable above:")
    print(f"   - Click '+ New application setting'")
    print(f"   - Enter the Name exactly as shown")
    print(f"   - Enter your actual Value (replace example values)")
    print(f"   - Click 'OK'")
    print(f"6. Click 'Save' at the top")
    print(f"7. Click 'Continue' to restart your app")
    
    print(f"\n🔒 SECURITY RECOMMENDATIONS:")
    print(f"{'='*80}")
    print(f"• Use strong, unique passwords different from local development")
    print(f"• SECRET_KEY must be a long, random string for production")
    print(f"• Store sensitive values in Azure Key Vault for enhanced security")
    print(f"• Never use the same passwords in local .env and Azure Portal")
    print(f"• Regularly rotate passwords and secret keys")
    
    print(f"\n✅ VARIABLES AUTOMATICALLY SET BY AZURE:")
    print(f"{'='*80}")
    azure_auto_vars = {
        'WEBSITE_SITE_NAME': 'Your app service name',
        'WEBSITE_RESOURCE_GROUP': 'Your resource group name', 
        'WEBSITE_HOSTNAME': 'Your app URL hostname',
        'PORT': 'Application port (usually 80 or 8000)',
        'WEBSITE_SKU': 'Your app service plan tier'
    }
    
    for name, description in azure_auto_vars.items():
        print(f"• {name}: {description}")
    
    print(f"\n🔄 DIFFERENCES FROM LOCAL ENVIRONMENT:")
    print(f"{'='*80}")
    print(f"LOCAL (.env file):")
    print(f"  - Uses SQLite database")
    print(f"  - Development/debug settings")
    print(f"  - Lower security requirements")
    print(f"  - File-based configuration")
    
    print(f"\nAZURE (Portal Application Settings):")
    print(f"  - Uses Azure SQL Database") 
    print(f"  - Production settings")
    print(f"  - High security requirements")
    print(f"  - Cloud-based configuration")
    print(f"  - Automatic scaling and management")

def compare_environments():
    """Compare local .env with what should be in Azure Portal"""
    
    print(f"\n🔄 LOCAL vs AZURE ENVIRONMENT COMPARISON")
    print(f"{'='*80}")
    
    # Load local .env if it exists
    local_vars = {}
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            import tempfile
            import shutil
            
            # Create a temporary environment to load .env without affecting current process
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp:
                shutil.copy('.env', tmp.name)
                temp_env = {}
                
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            local_vars[key.strip()] = value.strip()
            
            os.unlink(tmp.name)
        except Exception as e:
            print(f"⚠️ Could not read .env file: {e}")
    
    comparison_vars = [
        'SECRET_KEY', 'ADMIN_PASSWORD', 'FLASK_ENV', 'FLASK_DEBUG',
        'AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD'
    ]
    
    print(f"{'Variable':<25} | {'Local (.env)':<20} | {'Azure Portal':<20} | {'Notes'}")
    print(f"{'-'*25} | {'-'*20} | {'-'*20} | {'-'*20}")
    
    for var in comparison_vars:
        local_status = "✅ SET" if var in local_vars else "❌ MISSING"
        
        if var in ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']:
            azure_status = "✅ REQUIRED"
            notes = "Azure only"
        elif var == 'SECRET_KEY':
            azure_status = "✅ REQUIRED"
            notes = "Different value!"
        elif var == 'ADMIN_PASSWORD':
            azure_status = "✅ REQUIRED" 
            notes = "Different value!"
        elif var == 'FLASK_ENV':
            azure_status = "✅ SET"
            notes = "production"
        elif var == 'FLASK_DEBUG':
            azure_status = "✅ SET"
            notes = "False"
        else:
            azure_status = "⚙️ OPTIONAL"
            notes = "As needed"
        
        print(f"{var:<25} | {local_status:<20} | {azure_status:<20} | {notes}")

def main():
    """Main function"""
    print("🌐 Azure Portal Environment Variables Analysis")
    
    check_azure_portal_requirements()
    compare_environments()
    
    print(f"\n🎯 SUMMARY:")
    print(f"This analysis shows what should be configured in Azure Portal when deploying to Azure.")
    print(f"Local environment uses .env files, Azure uses Portal Application Settings.")
    print(f"Both environments need different values for security variables!")

if __name__ == "__main__":
    main()
