#!/usr/bin/env python3
"""
Azure startup script to ensure proper initialization
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import app, safe_init_db
    
    # Initialize database on startup (safely)
    print("Initializing database safely...")
    safe_init_db()
    print("Database initialized safely!")
    
    # Check if we can import all blueprints
    print("Testing blueprint imports...")
    from auth.routes import auth_bp
    from dashboard.routes import dashboard_bp  
    from learnings.routes import learnings_bp
    from admin.routes import admin_bp
    print("All blueprints imported successfully!")
    
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port)
        
except Exception as e:
    print(f"Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
