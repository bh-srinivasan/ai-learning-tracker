#!/usr/bin/env python3
"""
Gunicorn WSGI entry point for Azure App Service
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('NODE_ENV', 'production')

# Import the Flask app
from app import app

# Initialize database if needed
try:
    from app import init_db
    init_db()
    print("Database initialized for Gunicorn")
except Exception as e:
    print(f"Database initialization note: {e}")

# This is what Gunicorn will look for
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
