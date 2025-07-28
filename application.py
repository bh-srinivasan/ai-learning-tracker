#!/usr/bin/env python3
"""
Alternative entry point for Azure App Service
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set production environment
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Import and configure the app
from app import app

app.config['DEBUG'] = False
app.config['ENV'] = 'production'

# This is what Azure will look for
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=False)
