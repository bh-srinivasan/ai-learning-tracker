#!/usr/bin/env python3
"""
Test script to check if imports work correctly
"""

import sys
import os
import traceback

print("Testing imports for Azure deployment...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Test basic imports
try:
    import flask
    print(f"✅ Flask import successful: {flask.__version__}")
except Exception as e:
    print(f"❌ Flask import failed: {e}")
    traceback.print_exc()

try:
    import sqlite3
    print("✅ SQLite3 import successful")
except Exception as e:
    print(f"❌ SQLite3 import failed: {e}")

try:
    import requests
    print(f"✅ Requests import successful")
except Exception as e:
    print(f"❌ Requests import failed: {e}")

try:
    import azure.storage.blob
    print("✅ Azure Storage import successful")
except Exception as e:
    print(f"❌ Azure Storage import failed: {e}")

# Test our modules
try:
    from security_guard import ProductionSafetyError
    print("✅ Security guard import successful")
except Exception as e:
    print(f"❌ Security guard import failed: {e}")

try:
    from production_config import ProductionConfig
    print("✅ Production config import successful")
except Exception as e:
    print(f"❌ Production config import failed: {e}")

try:
    from production_safety_guard import ProductionSafetyGuard
    print("✅ Production safety guard import successful")
except Exception as e:
    print(f"❌ Production safety guard import failed: {e}")

# Test Azure database sync (optional)
try:
    from azure_database_sync import AzureDatabaseSync
    print("✅ Azure database sync import successful")
except Exception as e:
    print(f"⚠️ Azure database sync import failed (optional): {e}")

# Try importing our main app
try:
    print("\nTesting main app import...")
    from app import app
    print("✅ Main app import successful")
    print(f"App name: {app.name}")
    print(f"App config keys: {list(app.config.keys())}")
except Exception as e:
    print(f"❌ Main app import failed: {e}")
    traceback.print_exc()

print("\nImport test completed.")
