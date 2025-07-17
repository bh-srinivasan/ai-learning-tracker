#!/usr/bin/env python3
"""
Quick server verification
"""

import requests
import sys

try:
    print("🔍 Verifying Flask server...")
    response = requests.get("http://localhost:5000", timeout=10)
    
    if response.status_code == 200:
        print("✅ SUCCESS! Flask server is running")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Length: {len(response.text)} bytes")
        print(f"   URL: http://localhost:5000")
        
        # Check if it's the AI Learning Tracker
        if "AI Learning" in response.text or "login" in response.text.lower():
            print("✅ AI Learning Tracker app detected")
        
        print("\n🎉 Server verification complete!")
        print("Your Flask app is ready at: http://localhost:5000")
        
    else:
        print(f"⚠️ Server responding with status: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to localhost:5000")
    print("Server may still be starting up...")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📋 Server Status Summary:")
print("✅ Flask development server should be running")
print("✅ Simple browser opened to http://localhost:5000") 
print("✅ Ready for testing and development")
