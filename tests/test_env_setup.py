#!/usr/bin/env python3
"""
Test script to verify environment variable integration with Flask app
"""

import os
import sys
from dotenv import load_dotenv

def test_env_loading():
    """Test environment variable loading"""
    print("🧪 Testing Environment Variable Integration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Test critical variables
    test_vars = {
        'ADMIN_PASSWORD': os.environ.get('ADMIN_PASSWORD'),
        'DEMO_PASSWORD': os.environ.get('DEMO_PASSWORD'),
        'FLASK_SECRET_KEY': os.environ.get('FLASK_SECRET_KEY'),
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'development'),
        'SESSION_TIMEOUT': os.environ.get('SESSION_TIMEOUT', '3600')
    }
    
    success = True
    
    for var_name, var_value in test_vars.items():
        if var_value:
            # Hide sensitive values
            display_value = "***SET***" if any(x in var_name for x in ['PASSWORD', 'SECRET', 'KEY']) else var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ All environment variables loaded successfully!")
        print("🚀 Flask app should start with secure credentials from .env file")
    else:
        print("❌ Some environment variables are missing!")
        print("💡 Make sure your .env file exists and contains all required variables")
        sys.exit(1)

def test_password_security():
    """Test password security requirements"""
    print("\n🔒 Testing Password Security")
    print("=" * 30)
    
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    demo_password = os.environ.get('DEMO_PASSWORD', '')
    
    warnings = []
    
    if admin_password == 'admin':
        warnings.append("⚠️  Admin password is using default value")
    elif len(admin_password) < 8:
        warnings.append("⚠️  Admin password is less than 8 characters")
    
    if demo_password == 'bharath':
        warnings.append("⚠️  Demo password is using default value")
    elif len(demo_password) < 8:
        warnings.append("⚠️  Demo password is less than 8 characters")
    
    if warnings:
        print("Security Warnings:")
        for warning in warnings:
            print(f"   {warning}")
        print("\n💡 Consider updating passwords in .env file for better security")
    else:
        print("✅ Passwords meet security requirements")

if __name__ == "__main__":
    test_env_loading()
    test_password_security()
    
    print("\n🎯 Next Steps:")
    print("   1. Start the Flask app: python app.py")
    print("   2. Visit: http://localhost:5000")
    print("   3. Login with credentials from .env file")
    print("   4. Update .env file with stronger passwords for production")
