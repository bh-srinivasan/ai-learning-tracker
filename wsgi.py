"""
WSGI entry point for Azure App Service deployment.
This file ensures proper application startup on Azure.
"""

import os
import sys
import logging
from pathlib import Path

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for production deployment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'False')

logger.info(f"Starting WSGI application from {project_root}")
logger.info(f"Python path: {sys.path}")
logger.info(f"Environment: {os.environ.get('FLASK_ENV')}")

try:
    # Import the Flask application
    logger.info("Attempting to import Flask app...")
    from app import app
    logger.info("✅ Flask app imported successfully")

    # Configure the application for WSGI deployment
    application = app
    logger.info("✅ WSGI application configured")

except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    # Create a minimal Flask app if main app fails to import
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/health')
    def emergency_health():
        return f"Import error: {str(e)}", 500
    
    @application.route('/')
    def emergency_root():
        return f"Application startup error: {str(e)}", 500
    
    logger.info("Created emergency Flask app")

except Exception as e:
    logger.error(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal Flask app
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/health')
    def emergency_health():
        return f"Startup error: {str(e)}", 500
    
    @application.route('/')
    def emergency_root():
        return f"Application error: {str(e)}", 500

if __name__ == "__main__":
    # For direct execution (development)
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Running application on port {port}")
    application.run(host='0.0.0.0', port=port, debug=False)
