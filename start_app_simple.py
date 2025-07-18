#!/usr/bin/env python3
"""
Simple script to start the Flask app and verify all routes work
"""
import subprocess
import sys
import os

def start_flask_app():
    """Start the Flask app with proper environment"""
    try:
        # Change to the project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        print("Starting Flask app...")
        print(f"Project directory: {project_dir}")
        
        # Start the Flask app
        result = subprocess.run([sys.executable, "app.py"], 
                              capture_output=False, 
                              text=True)
        
        return result.returncode
        
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        return 1

if __name__ == "__main__":
    start_flask_app()
