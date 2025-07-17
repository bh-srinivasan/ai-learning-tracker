#!/usr/bin/env python3

# Simple server starter
if __name__ == "__main__":
    import app
    print("🚀 Starting AI Learning Tracker Server")
    print("=" * 50)
    print("🌐 URL: http://localhost:5000")
    print("🔑 Admin Login: admin / [check environment]")
    print("🔑 Demo Login: demo / [check environment]")
    print("=" * 50)
    
    try:
        app.app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except Exception as e:
        print(f"Error starting server: {e}")
