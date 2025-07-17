#!/usr/bin/env python3
"""
Diagnostic startup for Azure - Minimal test
"""
import os
import sys

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('NODE_ENV', 'production')

print("Starting diagnostic...")

try:
    # Test basic Flask import
    from flask import Flask
    print("✅ Flask import OK")
    
    # Test basic app creation
    test_app = Flask(__name__)
    print("✅ Flask app creation OK")
    
    @test_app.route('/')
    def hello():
        return "Diagnostic: App is working!"
    
    @test_app.route('/health')
    def health():
        return {"status": "ok", "message": "Diagnostic app running"}
    
    print("✅ Basic routes created")
    
    # This is what will run
    application = test_app
    
    if __name__ == "__main__":
        port = int(os.environ.get('PORT', 8000))
        print(f"✅ Starting diagnostic app on port {port}")
        test_app.run(host='0.0.0.0', port=port, debug=False)
        
except Exception as e:
    print(f"❌ Diagnostic failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
