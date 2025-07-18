#!/usr/bin/env python3
"""
Azure File Check
================
Simple script to verify files exist in Azure deployment.
"""

import os
import sys

def check_azure_files():
    """Check if required files exist"""
    
    print("=== AZURE FILE VERIFICATION ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print()
    
    # Check for required files
    required_files = [
        'app.py',
        'initialize_azure_admin.py',
        'ai_learning.db',
        'requirements.txt'
    ]
    
    print("📁 Checking for required files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - Found")
        else:
            print(f"❌ {file} - Missing")
    
    print()
    print("📂 Directory contents:")
    try:
        files = os.listdir('.')
        for f in sorted(files)[:20]:  # Show first 20 files
            print(f"   {f}")
        if len(files) > 20:
            print(f"   ... and {len(files) - 20} more files")
    except Exception as e:
        print(f"Error listing directory: {e}")
    
    print()
    print("🔍 Environment variables:")
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    if admin_pwd:
        print(f"✅ ADMIN_PASSWORD is set (length: {len(admin_pwd)})")
    else:
        print("❌ ADMIN_PASSWORD not found in environment")
    
    demo_pwd = os.environ.get('DEMO_PASSWORD')  
    if demo_pwd:
        print(f"✅ DEMO_PASSWORD is set (length: {len(demo_pwd)})")
    else:
        print("⚠️ DEMO_PASSWORD not found (will use default)")

if __name__ == "__main__":
    check_azure_files()
