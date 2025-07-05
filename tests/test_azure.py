#!/usr/bin/env python3
"""
Minimal Azure deployment test
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Azure Test App is Running!</h1><p>If you see this, the basic Flask app is working.</p>"

@app.route('/test-db')
def test_db():
    try:
        import sqlite3
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        return f"<h1>Database Test Successful!</h1><p>Result: {result}</p>"
    except Exception as e:
        return f"<h1>Database Error</h1><p>Error: {str(e)}</p>"

@app.route('/test-imports')
def test_imports():
    try:
        from auth.routes import auth_bp
        from dashboard.routes import dashboard_bp  
        from learnings.routes import learnings_bp
        from admin.routes import admin_bp
        return "<h1>Import Test Successful!</h1><p>All blueprints imported successfully.</p>"
    except Exception as e:
        return f"<h1>Import Error</h1><p>Error: {str(e)}</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
