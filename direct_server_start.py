#!/usr/bin/env python3
"""
Direct Flask server starter with verification
"""

import os
import sys
import time
import subprocess
import requests
from threading import Thread

def start_flask_server():
    """Start the Flask server"""
    try:
        print("🚀 Starting Flask Server...")
        # Import and run the app
        import app
        app.app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def verify_server():
    """Verify the server is running"""
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    for attempt in range(1, 11):
        try:
            print(f"🔍 Attempt {attempt}/10: Testing http://localhost:5000")
            response = requests.get("http://localhost:5000", timeout=5)
            
            if response.status_code == 200:
                print("✅ SUCCESS! Server is running and responding")
                print(f"   Status Code: {response.status_code}")
                print(f"   URL: http://localhost:5000")
                return True
                
        except requests.exceptions.ConnectionError:
            print(f"   ⏳ Connection refused (attempt {attempt})")
            time.sleep(2)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            time.sleep(2)
    
    print("❌ Server failed to respond after 10 attempts")
    return False

if __name__ == "__main__":
    print("🌐 AI Learning Tracker - Server Startup")
    print("=" * 50)
    
    # Start server in a separate thread
    server_thread = Thread(target=start_flask_server, daemon=True)
    server_thread.start()
    
    # Verify server is working
    if verify_server():
        print("\n🎉 Flask Server Successfully Started!")
        print("📋 Server Information:")
        print("   URL: http://localhost:5000")
        print("   Status: Running")
        print("   Environment: Development")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
    else:
        print("\n❌ Failed to start Flask server")
        sys.exit(1)
