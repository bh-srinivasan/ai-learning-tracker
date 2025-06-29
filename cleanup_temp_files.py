#!/usr/bin/env python3
"""
Cleanup Temporary Files
=====================

Remove all temporary test files, documentation, and scripts created during deployment.
"""

import os
import glob

def cleanup_temp_files():
    print("🧹 CLEANING UP TEMPORARY FILES")
    print("=" * 40)
    
    # List of temporary files and patterns to remove
    temp_files = [
        # Migration and test files
        'migration_route.py',
        'update_azure_passwords.py',
        'test_env_variables.py',
        'test_linkedin_courses.py',
        'test_complete_deployment.py',
        'azure_status_summary.py',
        'check_env_status.py',
        'test_azure_functionality.py',
        'check_azure_status.py',
        
        # Setup and configuration scripts
        'setup_azure_env_vars.py',
        'set_azure_env_vars.ps1',
        'set_azure_env_vars.sh',
        'set_my_env_vars.ps1',
        'set_minimal_env_vars.ps1',
        'set_production_env.ps1',
        'restart_azure_app.ps1',
        
        # Database migration scripts
        'fix_database_issues.py',
        'fix_admin_entries.py',
        'inspect_database.py',
        'analyze_global_learnings.py',
        
        # Password management scripts
        'reset_admin_password.py',
        'reset_admin_env_password.py',
        'reset_all_passwords.py',
        'safe_password_reset.py',
        'find_admin_password.py',
        
        # Test and validation scripts
        'test_env_setup.py',
        'test_login_credentials.py',
        'test_points_configuration.py',
        'env_manager.py',
        
        # Deployment scripts
        'prepare_deployment.py',
        'migrate_workspace.ps1',
        
        # Documentation files
        'ADMIN_PASSWORD_RESET_COMPLETE.md',
        'AZURE_DEPLOYMENT_SUCCESS.md',
        'DATABASE_FIXES_COMPLETE.md',
        'DEMO_USER_SETUP_COMPLETE.md',
        'DEPLOYMENT_COMPLETE_SUMMARY.md',
        'ENV_SETUP_DOCS.md',
        'FINAL_DEPLOYMENT_SUMMARY.md',
        'MIGRATION_SUCCESS_REPORT.md',
        'POINTS_CONFIG_FIX_REPORT.md',
        'FINAL_MIGRATION_STEPS.md',
        
        # Summary files
        'deployment_success_summary.py',
        'deployment_with_backend_reset_summary.py',
        'backend_password_implementation_summary.py',
        
        # This cleanup script itself
        'cleanup_temp_files.py'
    ]
    
    removed_count = 0
    
    for file_path in temp_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
        else:
            print(f"⚪ Not found: {file_path}")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   Removed {removed_count} temporary files")
    print(f"   Workspace cleaned up")
    
    # Also clean up any .pyc files
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"✅ Removed: {pyc_file}")
            removed_count += 1
        except:
            pass
    
    print(f"\n🎉 CLEANUP COMPLETE!")
    print(f"   Total files removed: {removed_count}")
    print(f"   Workspace is now clean and ready for production")

if __name__ == "__main__":
    cleanup_temp_files()
