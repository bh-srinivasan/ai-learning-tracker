#!/usr/bin/env python3
"""
Simple test application for Azure debugging
"""

from flask import Flask
import os
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    return f"""
    <h1>Azure Test App Working!</h1>
    <p>Python version: {sys.version}</p>
    <p>Current directory: {os.getcwd()}</p>
    <p>Environment: {os.environ.get('FLASK_ENV', 'not set')}</p>
    <p>Files in directory: {os.listdir('.')[:10]}</p>
    """

@app.route('/health')
def health():
    return {"status": "ok", "message": "Simple app is working"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
