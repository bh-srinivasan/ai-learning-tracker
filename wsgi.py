#!/usr/bin/env python3
"""
Gunicorn WSGI entry point for Azure App Service - SECURE VERSION
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('NODE_ENV', 'production')

# Import the Flask app
from app import app

# SECURE database initialization - preserves existing data
try:
    logger.info("WSGI: Initializing database SAFELY (preserving existing data)...")
    from app import safe_init_db, ensure_admin_exists
    
    # Safe initialization that preserves existing data
    safe_init_db()
    logger.info("WSGI: Database safely initialized")
    
    # Ensure admin exists
    ensure_admin_exists()
    logger.info("WSGI: Admin user verified")
    
    print("WSGI: Database initialized SAFELY for Gunicorn - existing data preserved")
    
except Exception as e:
    logger.error(f"WSGI Database initialization error: {e}")
    print(f"WSGI Database initialization note: {e}")

# This is what Gunicorn will look for
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
