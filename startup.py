#!/usr/bin/env python3
import os
import sys

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from app import app

if __name__ == "__main__":
    # Get port from environment variable or default to 8000 for Azure
    port = int(os.environ.get('PORT', 8000))
    
    # Azure requires binding to 0.0.0.0
    app.run(host='0.0.0.0', port=port, debug=False)
