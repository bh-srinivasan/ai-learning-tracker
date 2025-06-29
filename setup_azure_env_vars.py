#!/usr/bin/env python3
"""
Azure Environment Variables Setup Guide
======================================

This script provides instructions and commands to set up environment variables 
in Azure App Service for the AI Learning Tracker application.

Run this script to get the exact commands and values needed.
"""

def main():
    print("🌐 AZURE ENVIRONMENT VARIABLES SETUP")
    print("=" * 60)
    
    print("\n📋 REQUIRED ENVIRONMENT VARIABLES:")
    print("-" * 40)
    
    env_vars = {
        'ADMIN_PASSWORD': 'YourSecureAdminPassword123!',
        'DEMO_USERNAME': 'demo',
        'DEMO_PASSWORD': 'DemoUserPassword123!',
        'FLASK_SECRET_KEY': 'your-super-secret-key-change-this-in-production',
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': 'False',
        'DATABASE_URL': 'sqlite:///ai_learning.db',
        'SESSION_TIMEOUT': '3600'
    }
    
    for key, value in env_vars.items():
        print(f"✅ {key}: {value}")
    
    print("\n🛠️  AZURE CLI COMMANDS:")
    print("-" * 40)
    print("Run these commands in Azure CLI to set environment variables:")
    print()
    
    app_name = "ai-learning-tracker-bharath"
    resource_group = "AI_Learning_Tracker"
    
    for key, value in env_vars.items():
        print(f'az webapp config appsettings set --name {app_name} --resource-group {resource_group} --settings {key}="{value}"')
    
    print("\n🌐 AZURE PORTAL STEPS:")
    print("-" * 40)
    print("1. Go to: https://portal.azure.com")
    print("2. Navigate to: App Services > ai-learning-tracker-bharath")
    print("3. In the left menu, click: Configuration")
    print("4. Click: + New application setting")
    print("5. Add each environment variable:")
    print()
    
    for key, value in env_vars.items():
        print(f"   Name: {key}")
        print(f"   Value: {value}")
        print("   ---")
    
    print("\n6. Click 'Save' after adding all variables")
    print("7. Wait for the app to restart automatically")
    
    print("\n🔐 SECURITY NOTES:")
    print("-" * 40)
    print("• Change ADMIN_PASSWORD to a strong, unique password")
    print("• Change DEMO_PASSWORD to a secure demo password")
    print("• Change FLASK_SECRET_KEY to a random secret key")
    print("• These values should be different from your local .env file")
    
    print("\n🧪 TESTING AFTER SETUP:")
    print("-" * 40)
    print("After setting environment variables, test:")
    print("1. Login with admin credentials (from environment)")
    print("2. Login with demo credentials (from environment)")
    print("3. Check that 'bharath' user is protected")
    print("4. Test adding/editing learning entries")
    print("5. Test LinkedIn course functionality")
    
    print("\n🚀 VERIFICATION:")
    print("-" * 40)
    print("Run this command to test after setup:")
    print("python test_azure_functionality.py")
    
    print(f"\nProduction URL: https://{app_name}.azurewebsites.net")
    print("\n✅ Setup complete! Environment variables configured for production.")

if __name__ == "__main__":
    main()
