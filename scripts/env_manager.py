#!/usr/bin/env python3
"""
Environment Variable Management Utility
Helps manage and validate environment variables for the AI Learning Tracker
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def load_env_file(env_path='.env'):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        print(f"❌ Environment file {env_path} not found!")
        return False
    
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
    return True

def validate_env_vars():
    """Validate critical environment variables"""
    required_vars = [
        'ADMIN_PASSWORD',
        'DEMO_USERNAME',
        'DEMO_PASSWORD',
        'FLASK_SECRET_KEY'
    ]
    
    warnings = []
    errors = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            errors.append(f"❌ Missing required environment variable: {var}")
        elif var.endswith('_PASSWORD') and len(value) < 8:
            warnings.append(f"⚠️  Password {var} is less than 8 characters")
        elif var == 'FLASK_SECRET_KEY' and value == 'your-super-secret-key-change-this-in-production':
            warnings.append(f"⚠️  Using default value for {var} - change this in production!")
    
    # Check for default passwords
    if os.environ.get('ADMIN_PASSWORD') == 'admin':
        warnings.append("⚠️  ADMIN_PASSWORD is set to default value 'admin'")
    
    if os.environ.get('DEMO_PASSWORD') == 'demo':
        warnings.append("⚠️  DEMO_PASSWORD is set to default value 'demo'")
    
    # Check demo username
    demo_username = os.environ.get('DEMO_USERNAME', 'demo')
    if demo_username == 'demo':
        warnings.append("ℹ️  Using 'demo' as demo username for testing (recommended)")
    
    # Protected user notice
    warnings.append("🛡️  User 'bharath' is protected from testing modifications")
    
    return warnings, errors

def show_env_status():
    """Show current environment variable status"""
    print("\n🔍 Environment Variable Status:")
    print("=" * 50)
    
    env_vars = [
        'ADMIN_PASSWORD',
        'DEMO_USERNAME',
        'DEMO_PASSWORD', 
        'FLASK_SECRET_KEY',
        'FLASK_ENV',
        'FLASK_DEBUG',
        'SESSION_TIMEOUT',
        'PASSWORD_MIN_LENGTH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'Not Set')
        # Hide password values for security
        if 'PASSWORD' in var or 'SECRET' in var:
            display_value = "***HIDDEN***" if value != 'Not Set' else 'Not Set'
        else:
            display_value = value
        
        status = "✅" if value != 'Not Set' else "❌"
        print(f"{status} {var:<20}: {display_value}")

def main():
    """Main function"""
    print("🔧 AI Learning Tracker - Environment Variable Manager")
    print("=" * 60)
    
    # Load environment variables
    if not load_env_file():
        print("Creating example .env file...")
        return
    
    # Validate environment variables
    warnings, errors = validate_env_vars()
    
    # Show status
    show_env_status()
    
    # Show warnings and errors
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   {warning}")
    
    if errors:
        print("\n❌ Errors:")
        for error in errors:
            print(f"   {error}")
        sys.exit(1)
    
    if not warnings and not errors:
        print("\n✅ All environment variables are properly configured!")
    
    print("\n💡 Tips:")
    print("   - Never commit .env files to version control")
    print("   - Use strong, unique passwords in production")
    print("   - Change default secret keys before deployment")

if __name__ == "__main__":
    main()
