#!/usr/bin/env python3
"""
Minimal Azure Test - Test if Flask runs on Azure
"""

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>Azure Test - WORKING!</h1>
    <p>Flask is running successfully on Azure</p>
    <p>Environment: {}</p>
    <p>Python version: {}</p>
    '''.format(os.environ.get('ENV', 'unknown'), os.sys.version)

@app.route('/health')
def health():
    return {'status': 'healthy', 'env': os.environ.get('ENV', 'unknown')}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
