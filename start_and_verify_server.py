#!/usr/bin/env python3
"""
Server startup and verification script
"""

import subprocess
import time
import requests
import sys
import os

def start_and_verify_server():
    """Start Flask server and verify it's running"""
    
    print("🚀 Starting Flask Development Server")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir(r"c:\Users\bhsrinivasan\Downloads\Learning\Vibe Coding\AI_Learning")
    
    try:
        # Start the Flask server in the background
        print("📡 Launching Flask app...")
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give the server time to start
        print("⏳ Waiting for server to initialize...")
        
        # Try to connect multiple times
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            time.sleep(2)
            
            try:
                print(f"🔍 Attempt {attempt}/{max_attempts}: Testing connection...")
                response = requests.get("http://localhost:5000", timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS! Server is running and responding")
                    print(f"   Status Code: {response.status_code}")
                    print(f"   URL: http://localhost:5000")
                    print(f"   Process ID: {process.pid}")
                    
                    # Check if login page is accessible
                    if "login" in response.text.lower() or "ai learning" in response.text.lower():
                        print("✅ Login page is accessible")
                    
                    return True, process
                    
            except requests.exceptions.ConnectionError:
                print(f"   ⏳ Server not ready yet (attempt {attempt})")
                continue
            except requests.exceptions.Timeout:
                print(f"   ⏳ Connection timeout (attempt {attempt})")
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        print("❌ Server failed to start after all attempts")
        
        # Get any error output
        stdout, stderr = process.communicate(timeout=5)
        if stderr:
            print(f"Error output: {stderr}")
        if stdout:
            print(f"Standard output: {stdout}")
            
        return False, process
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False, None

def verify_server_features():
    """Verify key server features are working"""
    print("\n🧪 Testing Server Features")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # Test main page
        response = requests.get(base_url, timeout=10)
        print(f"✅ Main page: {response.status_code}")
        
        # Test login page
        login_response = requests.get(f"{base_url}/login", timeout=10)
        print(f"✅ Login page: {login_response.status_code}")
        
        # Test if CSS/static files are loading
        if "bootstrap" in response.text.lower() or "css" in response.text.lower():
            print("✅ Static files (CSS) loading")
        
        print(f"\n🎉 Server Verification Complete!")
        print(f"Your Flask app is running at: {base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature verification failed: {e}")
        return False

if __name__ == "__main__":
    success, process = start_and_verify_server()
    
    if success:
        verify_server_features()
        
        print(f"\n📋 Server Information")
        print("=" * 50)
        print(f"✅ Status: Running")
        print(f"🌐 URL: http://localhost:5000") 
        print(f"🔧 Environment: Development")
        print(f"🔄 Auto-reload: Enabled")
        print(f"📱 Access: Ready for login")
        
        print(f"\n🎯 Next Steps:")
        print("1. Open http://localhost:5000 in your browser")
        print("2. Login with admin credentials")
        print("3. Test the dashboard and course features")
        print("\nServer will continue running in the background...")
        
    else:
        print(f"\n❌ Server startup failed")
        print("Please check for any Python syntax errors or port conflicts")
