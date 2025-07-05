#!/usr/bin/env python3
"""
Test script to diagnose Flask app issues
"""

import sys
import os

print("=== Flask App Diagnostic ===")

# Test 1: Check Python environment
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

# Test 2: Check required imports
try:
    import flask
    print(f"✓ Flask version: {flask.__version__}")
except ImportError as e:
    print(f"✗ Flask not available: {e}")

try:
    import werkzeug
    print(f"✓ Werkzeug available")
except ImportError as e:
    print(f"✗ Werkzeug not available: {e}")

try:
    import sqlite3
    print(f"✓ SQLite3 available")
except ImportError as e:
    print(f"✗ SQLite3 not available: {e}")

# Test 3: Check if app.py can be imported
try:
    print("\n=== Testing app.py import ===")
    import app
    print("✓ app.py imported successfully")
    
    # Test database initialization
    print("Testing database initialization...")
    app.init_db()
    print("✓ Database initialized successfully")
    
    # Test Flask app creation
    print("Testing Flask app...")
    flask_app = app.app
    print(f"✓ Flask app created: {flask_app}")
    
    print("\n=== Starting Flask server ===")
    print("Server should start on http://localhost:5000")
    flask_app.run(debug=True, host='127.0.0.1', port=5000)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
