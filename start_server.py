#!/usr/bin/env python3
"""
Startup script for the Flask application
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("=== Starting AI Learning Tracker ===")
    print("Importing Flask app...")
    
    from app import app, init_db
    
    print("Initializing database...")
    init_db()
    
    print("Starting Flask server...")
    print("Server will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required packages are installed:")
    print("pip install flask werkzeug python-dotenv")
    
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("Application stopped.")
