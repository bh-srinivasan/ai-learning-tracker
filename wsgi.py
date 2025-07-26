"""
WSGI entry point for Azure App Service deployment.
This file ensures proper application startup on Azure.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for production deployment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'False')

try:
    # Import the Flask application
    from app import app

    # Add health check endpoint for Azure diagnostics
    @app.route('/health')
    def health_check():
        from health_check import check_health
        import json
        status = check_health()
        return json.dumps(status, indent=2), 200, {'Content-Type': 'application/json'}

    # Configure the application for WSGI deployment
    application = app

except Exception as e:
    # Create a minimal Flask app if main app fails to import
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/health')
    def emergency_health():
        return f"Application import failed: {str(e)}", 500
    
    @application.route('/')
    def emergency_root():
        return f"Application startup error: {str(e)}", 500

if __name__ == "__main__":
    # For direct execution (development)
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
