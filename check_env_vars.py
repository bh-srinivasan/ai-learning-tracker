#!/usr/bin/env python3
"""
Azure Environment Variable Checker
Securely validates that all required environment variables are set without exposing values
"""

import os
import sys
from datetime import datetime

class EnvironmentChecker:
    def __init__(self):
        self.required_production_vars = [
            'AZURE_SQL_SERVER',
            'AZURE_SQL_DATABASE', 
            'AZURE_SQL_USERNAME',
            'AZURE_SQL_PASSWORD',
            'ADMIN_PASSWORD'
        ]
        
        self.optional_vars = [
            'ENV',
            'ENVIRONMENT',
            'DATABASE_URL',
            'SECRET_KEY',
            'FLASK_ENV'
        ]

    def check_environment_variable(self, var_name):
        """Check if environment variable is set (without exposing value)"""
        value = os.environ.get(var_name)
        if value:
            return {
                'name': var_name,
                'status': 'SET',
                'length': len(value),
                'masked_value': f"{'*' * min(len(value), 10)}..." if len(value) > 3 else '***'
            }
        else:
            return {
                'name': var_name, 
                'status': 'NOT_SET',
                'length': 0,
                'masked_value': 'NOT_SET'
            }

    def validate_all_variables(self):
        """Validate all environment variables"""
        print("=" * 70)
        print("AZURE ENVIRONMENT VARIABLE VALIDATION")
        print("=" * 70)
        print(f"Timestamp: {datetime.now()}")
        print(f"Environment: {os.environ.get('ENV', 'not_set')}")
        print()
        
        results = {}
        all_valid = True
        
        # Check required variables
        print("REQUIRED PRODUCTION VARIABLES:")
        print("-" * 40)
        for var in self.required_production_vars:
            result = self.check_environment_variable(var)
            results[var] = result
            
            status_symbol = "✅" if result['status'] == 'SET' else "❌"
            print(f"{status_symbol} {var:25}: {result['status']:8} ({result['length']} chars)")
            
            if result['status'] != 'SET':
                all_valid = False
        
        print()
        print("OPTIONAL VARIABLES:")
        print("-" * 40)
        for var in self.optional_vars:
            result = self.check_environment_variable(var)
            results[var] = result
            
            status_symbol = "✅" if result['status'] == 'SET' else "⚪"
            print(f"{status_symbol} {var:25}: {result['status']:8} ({result['length']} chars)")
        
        print()
        print("VALIDATION SUMMARY:")
        print("-" * 40)
        
        if all_valid:
            print("✅ All required environment variables are properly set")
            print("✅ App can run in full production mode with Azure SQL")
        else:
            missing_vars = [var for var in self.required_production_vars 
                          if results[var]['status'] != 'SET']
            print(f"❌ Missing required variables: {missing_vars}")
            print("⚠️  App will run in limited mode (SQLite only)")
            print("\nTO FIX:")
            print("1. Set missing environment variables in Azure App Service")
            print("2. Go to: Azure Portal > App Services > Your App > Configuration")
            print("3. Add the missing variables to Application settings")
            print("4. Restart the App Service")
        
        return results, all_valid

    def generate_azure_config_script(self):
        """Generate Azure CLI script to set environment variables"""
        missing_vars = []
        for var in self.required_production_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if not missing_vars:
            print("\n✅ No Azure CLI script needed - all variables are set")
            return
        
        print("\n🔧 AZURE CLI CONFIGURATION SCRIPT:")
        print("-" * 40)
        print("# Run these commands to set missing environment variables")
        print("# Replace YOUR_APP_NAME with your actual App Service name")
        print("# Replace YOUR_RESOURCE_GROUP with your resource group name")
        print()
        
        app_name = "ai-learning-tracker-bharath"  # Based on previous deployment
        resource_group = "your-resource-group"
        
        for var in missing_vars:
            if var == 'AZURE_SQL_PASSWORD':
                print(f"az webapp config appsettings set --name {app_name} --resource-group {resource_group} --settings {var}='YOUR_SECURE_SQL_PASSWORD'")
            elif var == 'ADMIN_PASSWORD':
                print(f"az webapp config appsettings set --name {app_name} --resource-group {resource_group} --settings {var}='YOUR_SECURE_ADMIN_PASSWORD'")
            else:
                print(f"# {var} should be set to appropriate value")
        
        print("\n# After setting variables, restart the app:")
        print(f"az webapp restart --name {app_name} --resource-group {resource_group}")

def main():
    """Main function"""
    checker = EnvironmentChecker()
    
    try:
        results, all_valid = checker.validate_all_variables()
        
        if not all_valid:
            checker.generate_azure_config_script()
            sys.exit(1)  # Exit with error code if validation fails
        else:
            sys.exit(0)  # Exit successfully
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
