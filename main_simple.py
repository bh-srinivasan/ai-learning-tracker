#!/usr/bin/env python3
"""
Minimal Azure App Service Entry Point - Fixed for deployment
"""

import os
import sys
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Set production environment
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('FLASK_DEBUG', 'False')
    
    logger.info("Starting Azure deployment...")
    
    # Import the Flask app directly without complex initialization
    from app import app
    
    # Configure for production
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    
    logger.info("App imported and configured successfully")
    
except Exception as e:
    logger.error(f"Error importing app: {e}")
    # Create a minimal fallback app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return f"Startup error: {e}", 500

# For WSGI
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
