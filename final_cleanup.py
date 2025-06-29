#!/usr/bin/env python3
"""
Final Cleanup Script for AI Learning Tracker
Removes all temporary test files, debug scripts, and documentation
while preserving essential production files.
"""

import os
import sys

def main():
    """Remove all temporary files and keep only production-ready code."""
    
    # Files to remove - temporary test and debug files
    files_to_remove = [
        'admin_password_reset.py',
        'azure_account_setup.md',
        'AZURE_DEPLOYMENT_SESSION_CHECKLIST.md',
        'azure_deployment_steps.md',
        'BACKEND_PASSWORD_RESET_DOCS.md',
        'debug_endpoint.py',
        'DEPLOYMENT_GUIDE.md',
        'DEPLOYMENT_SUCCESS.md',
        'deploy_azure.md',
        'PASSWORD_CHANGE_FIX_REPORT.md',
        'render_deployment.md',
        'SECURE_PASSWORD_GENERATION_DOCS.md',
        'SESSION_MANAGEMENT.md',
        'startup.py',
        'test_admin_password.py',
        'test_azure_deployment.py',
        'test_backend_password_reset.py',
        'test_current_admin_password.py',
        'test_direct_password.py',
        'test_flask_password.py',
        'test_generate_password.py',
        'test_manage_users_ui.py',
        'test_password_reset.py',
        'test_password_update.py',
        'test_ui_improvements.py',
        'test_view_password_removal.py',
        'ui_verification_summary.py',
        'view_password_removal_summary.py',
        'final_cleanup.py'  # This script itself
    ]
    
    removed_count = 0
    
    print("🧹 Starting final cleanup of AI Learning Tracker workspace...")
    
    # Remove temporary files
    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✅ Removed: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {filename}: {e}")
        else:
            print(f"⚠️  Not found: {filename}")
    
    # Clean up __pycache__ directories
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_dirs.append(os.path.join(root, '__pycache__'))
    
    for pycache_dir in pycache_dirs:
        try:
            import shutil
            shutil.rmtree(pycache_dir)
            print(f"✅ Removed __pycache__: {pycache_dir}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Error removing {pycache_dir}: {e}")
    
    print(f"\n🎉 Cleanup complete! Removed {removed_count} items.")
    print("\n📂 Remaining production files:")
    
    # List remaining files
    production_files = [
        'app.py',
        'config.py',
        'production_config.py',
        'requirements.txt',
        'web.config',
        'README.md',
        '.gitignore',
        '.env',
        'ai_learning.db'
    ]
    
    production_dirs = [
        'admin/',
        'auth/', 
        'courses/',
        'dashboard/',
        'learnings/',
        'recommendations/',
        'static/',
        'templates/'
    ]
    
    for file in production_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ Missing: {file}")
    
    for dir_name in production_dirs:
        if os.path.exists(dir_name):
            print(f"📁 {dir_name}")
        else:
            print(f"❌ Missing directory: {dir_name}")
    
    print("\n🚀 Workspace is now production-ready!")

if __name__ == "__main__":
    main()
