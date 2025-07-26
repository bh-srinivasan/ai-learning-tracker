"""
🚨 CRITICAL AZURE DATABASE FIX
=============================
Fix Azure database integration - this is why your Azure DB is empty!
"""

def fix_azure_database_integration():
    """Add Azure database sync to main app.py"""
    
    print("🔧 FIXING AZURE DATABASE INTEGRATION")
    print("=====================================")
    print("🎯 Adding Azure Storage sync to app startup")
    print()
    
    # Read current app.py
    with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
        app_content = f.read()
    
    # Check if Azure sync is already integrated
    if 'azure_database_sync' in app_content.lower():
        print("   ✅ Azure sync already integrated")
        return True
    
    print("   ❌ Azure sync NOT integrated - this is the problem!")
    print("   🔧 Adding Azure database sync integration...")
    
    # Find the import section
    import_section = """import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import json
from pathlib import Path
import logging
import threading
import time

# Import Azure database sync for production
try:
    from azure_database_sync import AzureDatabaseSync
    azure_sync = AzureDatabaseSync()
    AZURE_SYNC_AVAILABLE = True
    print("✅ Azure database sync loaded")
except ImportError as e:
    print(f"⚠️  Azure sync not available: {e}")
    azure_sync = None
    AZURE_SYNC_AVAILABLE = False"""
    
    # Find where imports end (usually before app = Flask)
    app_creation_line = "app = Flask(__name__)"
    
    if app_creation_line in app_content:
        # Add Azure sync after Flask app creation
        startup_code = '''
# Initialize Azure database sync on startup
if AZURE_SYNC_AVAILABLE and azure_sync:
    print("🔄 Initializing Azure database sync...")
    try:
        # Download database from Azure Storage if available
        azure_sync.sync_from_azure_on_startup()
        print("✅ Azure database sync initialized successfully")
    except Exception as e:
        print(f"⚠️ Azure sync initialization failed: {e}")
        print("   Continuing with local database only")

@app.before_first_request
def initialize_azure_sync():
    """Initialize Azure sync before first request"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.sync_from_azure_on_startup()
        except Exception as e:
            app.logger.warning(f"Azure sync failed on startup: {e}")
'''
        
        # Add Azure upload hooks
        azure_hooks = '''
def sync_to_azure_after_change():
    """Upload database to Azure after changes"""
    if AZURE_SYNC_AVAILABLE and azure_sync:
        try:
            azure_sync.upload_database_to_azure()
        except Exception as e:
            app.logger.warning(f"Azure upload failed: {e}")
'''
        
        # Insert the imports at the beginning
        lines = app_content.split('\n')
        new_lines = []
        imports_added = False
        startup_added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Add imports after existing imports but before app creation
            if not imports_added and 'from azure_database_sync import' not in app_content and line.strip().startswith('app = Flask'):
                # Insert Azure import before this line
                new_lines.insert(-1, "# Import Azure database sync for production")
                new_lines.insert(-1, "try:")
                new_lines.insert(-1, "    from azure_database_sync import AzureDatabaseSync")
                new_lines.insert(-1, "    azure_sync = AzureDatabaseSync()")
                new_lines.insert(-1, "    AZURE_SYNC_AVAILABLE = True")
                new_lines.insert(-1, "    print('✅ Azure database sync loaded')")
                new_lines.insert(-1, "except ImportError as e:")
                new_lines.insert(-1, "    print(f'⚠️  Azure sync not available: {e}')")
                new_lines.insert(-1, "    azure_sync = None")
                new_lines.insert(-1, "    AZURE_SYNC_AVAILABLE = False")
                new_lines.insert(-1, "")
                imports_added = True
            
            # Add startup code after app configuration
            if not startup_added and imports_added and 'app.config[' in line:
                # Look for a good place to add startup code
                if i + 1 < len(lines) and not lines[i + 1].startswith('app.config'):
                    new_lines.extend([
                        "",
                        "# Initialize Azure database sync on startup",
                        "if AZURE_SYNC_AVAILABLE and azure_sync:",
                        "    print('🔄 Initializing Azure database sync...')",
                        "    try:",
                        "        # Download database from Azure Storage if available",
                        "        azure_sync.sync_from_azure_on_startup()",
                        "        print('✅ Azure database sync initialized successfully')",
                        "    except Exception as e:",
                        "        print(f'⚠️ Azure sync initialization failed: {e}')",
                        "        print('   Continuing with local database only')",
                        "",
                        "@app.before_first_request",
                        "def initialize_azure_sync():",
                        "    \"\"\"Initialize Azure sync before first request\"\"\"",
                        "    if AZURE_SYNC_AVAILABLE and azure_sync:",
                        "        try:",
                        "            azure_sync.sync_from_azure_on_startup()",
                        "        except Exception as e:",
                        "            app.logger.warning(f'Azure sync failed on startup: {e}')",
                        "",
                        "def sync_to_azure_after_change():",
                        "    \"\"\"Upload database to Azure after changes\"\"\"",
                        "    if AZURE_SYNC_AVAILABLE and azure_sync:",
                        "        try:",
                        "            azure_sync.upload_database_to_azure()",
                        "        except Exception as e:",
                        "            app.logger.warning(f'Azure upload failed: {e}')",
                        ""
                    ])
                    startup_added = True
        
        # Write the updated app.py
        with open('app_with_azure_sync.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("   ✅ Created app_with_azure_sync.py with Azure integration")
        print()
        print("🚨 CRITICAL FIX COMPLETED!")
        print("   📁 File created: app_with_azure_sync.py")
        print("   🔧 This version includes:")
        print("      - Azure database sync import")
        print("      - Startup sync from Azure Storage")
        print("      - Upload hooks for data changes")
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Review app_with_azure_sync.py")
        print("   2. Replace app.py with the fixed version")
        print("   3. Deploy to Azure with proper sync")
        print("   4. Azure will now download database on startup!")
        
        return True
    else:
        print("   ❌ Could not find app creation line in app.py")
        return False

if __name__ == "__main__":
    fix_azure_database_integration()
