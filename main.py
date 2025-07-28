#!/usr/bin/env python3
"""
Azure App Service Entry Point
Optimized for Azure App Service deployment
"""

import os
import sys
import logging

# Configure logging for Azure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

logger.info(f"Starting application from: {current_dir}")
logger.info(f"Python path: {sys.path[:3]}")

try:
    # Set environment for Azure
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('FLASK_DEBUG', 'False')
    
    logger.info("Environment variables set")
    
    # Import the Flask app
    from app import app
    
    logger.info("App imported successfully")
    
    # Configure for production
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    app.config['TESTING'] = False
    
    # Set secret key if not provided
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-me')
    
    logger.info("App configured for production")
    
    # Log some basic info
    logger.info(f"App name: {app.name}")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Environment: {app.config.get('ENV')}")
    
    # Test that the app can handle requests
    with app.test_request_context():
        logger.info("Test request context works")
    
    logger.info("App initialization complete")
    
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Files in directory: {os.listdir('.')}")
    raise
except Exception as e:
    logger.error(f"Error during app initialization: {e}")
    raise

# For direct execution
if __name__ == "__main__":
    logger.info("Running app directly")
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=False
    )
else:
    logger.info("App loaded for WSGI server")

# Export for WSGI
application = app
