#!/usr/bin/env python3
"""
Debug Azure Environment Variables
This script helps debug what environment variables are available in Azure
"""

import os
import json
from datetime import datetime

def debug_azure_environment():
    """Debug Azure environment variables"""
    print("=" * 60)
    print("AZURE ENVIRONMENT VARIABLE DEBUG")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check key environment variables
    env_vars_to_check = [
        'ENV',
        'ENVIRONMENT', 
        'AZURE_SQL_SERVER',
        'AZURE_SQL_DATABASE',
        'AZURE_SQL_USERNAME',
        'AZURE_SQL_PASSWORD',
        'ADMIN_PASSWORD',
        'DATABASE_URL',
        'PYTHONPATH',
        'WEBSITE_SITE_NAME',
        'WEBSITE_RESOURCE_GROUP'
    ]
    
    print("KEY ENVIRONMENT VARIABLES:")
    print("-" * 40)
    for var in env_vars_to_check:
        value = os.environ.get(var)
        if var in ['AZURE_SQL_PASSWORD', 'ADMIN_PASSWORD']:
            # Mask sensitive values
            display_value = "***MASKED***" if value else "NOT SET"
        else:
            display_value = value if value else "NOT SET"
        print(f"{var:25}: {display_value}")
    
    print()
    print("ALL ENVIRONMENT VARIABLES:")
    print("-" * 40)
    
    # Get all environment variables but mask sensitive ones
    all_env = {}
    sensitive_keywords = ['password', 'secret', 'key', 'token', 'auth']
    
    for key, value in os.environ.items():
        if any(keyword in key.lower() for keyword in sensitive_keywords):
            all_env[key] = "***MASKED***"
        else:
            all_env[key] = value
    
    # Sort and display
    for key in sorted(all_env.keys()):
        print(f"{key:35}: {all_env[key]}")
    
    print()
    print("AZURE-SPECIFIC VARIABLES:")
    print("-" * 40)
    azure_vars = {k: v for k, v in all_env.items() if 'azure' in k.lower() or 'website' in k.lower()}
    for key in sorted(azure_vars.keys()):
        print(f"{key:35}: {azure_vars[key]}")
    
    return {
        'key_vars': {var: os.environ.get(var) for var in env_vars_to_check},
        'azure_vars': azure_vars,
        'total_env_vars': len(os.environ)
    }

if __name__ == "__main__":
    result = debug_azure_environment()
    
    # Save to file for analysis
    with open('azure_env_debug.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n✅ Debug info saved to azure_env_debug.json")
    print(f"✅ Total environment variables found: {result['total_env_vars']}")
