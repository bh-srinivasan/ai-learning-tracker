"""
Flask Server Verification Tool
==============================

Simple tool to verify Flask server status
"""

import requests
import socket
import time

def check_flask_server():
    """Check if Flask server is running and responding"""
    
    print("🔍 Flask Server Status Check")
    print("=" * 30)
    
    # Check 1: Port availability
    print("1. Checking port 5000...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('localhost', 5000))
        if result == 0:
            print("   ✅ Port 5000 is in use")
            port_open = True
        else:
            print("   ❌ Port 5000 is not in use")
            port_open = False
    except Exception as e:
        print(f"   ❌ Error checking port: {e}")
        port_open = False
    finally:
        sock.close()
    
    # Check 2: HTTP Response
    print("2. Testing HTTP response...")
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print(f"   ✅ Server responded: {response.status_code}")
        
        if response.status_code == 302:
            print("   📝 Redirect detected (likely to login page)")
        elif response.status_code == 200:
            print("   📝 Direct response received")
            
        http_working = True
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection refused - server not running")
        http_working = False
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout")
        http_working = False
    except Exception as e:
        print(f"   ❌ HTTP Error: {e}")
        http_working = False
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 15)
    
    if port_open and http_working:
        print("🎉 Flask server is RUNNING and RESPONDING!")
        print("🌐 Access: http://localhost:5000")
        print("🔑 Login: demo / demo")
        return True
    elif port_open and not http_working:
        print("⚠️  Server process running but not responding to HTTP")
        return False
    else:
        print("❌ Flask server is NOT running")
        return False

if __name__ == "__main__":
    check_flask_server()
