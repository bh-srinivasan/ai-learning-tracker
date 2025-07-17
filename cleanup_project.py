#!/usr/bin/env python3
"""
Project Cleanup Script for AI Learning Tracker
Removes temporary files, test files, and outdated documentation
"""

import os
import shutil
from pathlib import Path

# Files and directories to keep (core project files)
KEEP_FILES = {
    # Core application files
    'app.py',
    'level_manager.py',
    'config.py',
    'requirements.txt',
    'web.config',
    '.env',
    '.gitignore',
    
    # Documentation
    'README.md',
    'GITHUB_AZURE_DEPLOYMENT_GUIDE.md',
    'GITHUB_AUTHENTICATION_GUIDE.md',
    'DEPLOYMENT_GUIDE.md',
    'FINAL_MIGRATION_STEPS.md',
    
    # Core directories
    'admin',
    'auth', 
    'dashboard',
    'learnings',
    'courses',
    'recommendations',
    'static',
    'templates',
    '.git',
    '.github',
    '.venv',
    '.vscode',
    '__pycache__',
    
    # Database and deployment
    'ai_learning.db',
    'deploy_azure_secure.py',  # Keep main deployment script
    'production_config.py',
}

# Patterns for files to remove
REMOVE_PATTERNS = [
    # Test files
    'test_*.py',
    '*_test.py',
    
    # Debug and temporary files  
    'debug_*.py',
    'debug_*.html',
    'analyze_*.py',
    'check_*.py',
    'cleanup_*.py',
    'final_*.py',
    'fix_*.py',
    'inspect_*.py',
    'reset_*.py',
    'safe_*.py',
    'setup_*.py',
    'sorting_*.py',
    'validate_*.py',
    'ui_*.py',
    'professional_*.py',
    'native_*.py',
    'refactoring_*.py',
    
    # Environment and Azure setup files
    'azure_*.py',
    'env_*.py',
    'set_*.ps1',
    'set_*.sh',
    'restart_*.ps1',
    'update_*.py',
    'prepare_*.py',
    
    # Report and summary files
    '*_REPORT.md',
    '*_SUCCESS.md', 
    '*_COMPLETE.md',
    '*_SUMMARY.md',
    '*_DOCS.md',
    'ENHANCED_*.md',
    'PROFESSIONAL_*.md',
    'WORKSPACE_*.md',
    'UI_*.md',
    'LEVEL_*.md',
    'PROFILE_*.md',
    'DATABASE_*.md',
    'DEMO_*.md',
    'ADMIN_*.md',
    'AZURE_*.md',
    'DEPLOYMENT_SUCCESS.md',
    'DEPLOYMENT_COMPLETE_SUMMARY.md',
    
    # Log files
    'deployment_log.txt',
    '*.log',
    
    # Deploy scripts (keep only main one)
    'deploy_secure.py',
    'deploy.ps1',
]

def should_remove(file_path):
    """Check if a file should be removed based on patterns"""
    file_name = file_path.name
    
    # Never remove files in KEEP_FILES
    if file_name in KEEP_FILES:
        return False
    
    # Never remove directories that are in KEEP_FILES
    if file_path.is_dir() and file_name in KEEP_FILES:
        return False
    
    # Check removal patterns
    for pattern in REMOVE_PATTERNS:
        if file_path.match(pattern):
            return True
    
    return False

def cleanup_project():
    """Main cleanup function"""
    project_root = Path('.')
    removed_files = []
    kept_files = []
    
    print("🧹 Starting AI Learning Tracker project cleanup...")
    print("=" * 60)
    
    # Get all files and directories
    all_items = list(project_root.iterdir())
    
    for item in all_items:
        if should_remove(item):
            try:
                if item.is_file():
                    item.unlink()
                    removed_files.append(str(item))
                    print(f"🗑️  Removed file: {item}")
                elif item.is_dir() and item.name not in KEEP_FILES:
                    shutil.rmtree(item)
                    removed_files.append(str(item))
                    print(f"🗑️  Removed directory: {item}")
            except Exception as e:
                print(f"❌ Error removing {item}: {e}")
        else:
            kept_files.append(str(item))
    
    print("\n" + "=" * 60)
    print(f"✅ Cleanup completed!")
    print(f"📁 Files/directories removed: {len(removed_files)}")
    print(f"📁 Files/directories kept: {len(kept_files)}")
    
    if removed_files:
        print(f"\n🗑️  Removed items:")
        for item in sorted(removed_files):
            print(f"   - {item}")
    
    print(f"\n📂 Remaining core files:")
    remaining_files = [f for f in kept_files if not f.startswith('.') and Path(f).is_file()]
    for item in sorted(remaining_files):
        print(f"   - {item}")

if __name__ == '__main__':
    cleanup_project()
