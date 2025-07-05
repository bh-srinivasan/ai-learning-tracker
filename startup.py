#!/usr/bin/env python3
"""
Azure startup script - Simplified for production
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('NODE_ENV', 'production')

try:
    # Import app first
    from app import app
    
    # Try to initialize database safely
    try:
        from app import init_db
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization warning: {e}")
        # Continue even if DB init fails - it might already exist
    
    print("App startup successful!")
    
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 8000))
        print(f"Starting app on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
except Exception as e:
    print(f"Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
        
except Exception as e:
    print(f"Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
