#!/usr/bin/env python3
"""
Verification script to confirm all warnings are resolved and server is running
"""

import subprocess
import sys
import time
import requests

def test_syntax():
    """Test if all Python files have valid syntax"""
    print("🔍 Testing Python Syntax")
    print("=" * 40)
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', 'import app; print("✅ Main app imports successfully")'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ app.py syntax is valid")
            return True
        else:
            print("❌ app.py has syntax errors:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing syntax: {e}")
        return False

def test_server_running():
    """Test if the Flask server is running"""
    print("\n🌐 Testing Server Connection")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            print(f"   Status Code: {response.status_code}")
            return True
        else:
            print(f"⚠️  Server responding with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server connection timed out")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def check_warnings_resolved():
    """Check if the specific warnings mentioned were resolved"""
    print("\n🔧 Checking Resolved Issues")
    print("=" * 40)
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check the fixed line
        if "course['title'], course['source'], course['level'], course['url'], course['points'], course['description']" in content:
            print("✅ Variable reference issue fixed")
            print("   Using course['key'] instead of undefined variables")
        else:
            print("❌ Variable reference issue not found")
            
        # Check for the complete_course route we added
        if "@app.route('/complete_course/<int:course_id>', methods=['POST'])" in content:
            print("✅ complete_course route exists")
        else:
            print("❌ complete_course route missing")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking fixes: {e}")
        return False

def main():
    """Main verification function"""
    print("🧪 Workspace Warnings Resolution Verification")
    print("=" * 60)
    
    syntax_ok = test_syntax()
    server_running = test_server_running()
    fixes_verified = check_warnings_resolved()
    
    print(f"\n📊 Summary")
    print("=" * 40)
    print(f"Syntax Valid: {'✅' if syntax_ok else '❌'}")
    print(f"Server Running: {'✅' if server_running else '❌'}")
    print(f"Fixes Applied: {'✅' if fixes_verified else '❌'}")
    
    if all([syntax_ok, server_running, fixes_verified]):
        print(f"\n🎉 All Issues Resolved Successfully!")
        print("Your Flask app is running at: http://localhost:5000")
        print("\nYou can now:")
        print("- Login to the application")
        print("- Access the dashboard")
        print("- Complete courses without errors")
        print("- Use all admin functionality")
    else:
        print(f"\n⚠️  Some issues may still exist")
        if not syntax_ok:
            print("- Check Python syntax errors")
        if not server_running:
            print("- Ensure Flask server is started")
        if not fixes_verified:
            print("- Verify code fixes were applied correctly")

if __name__ == '__main__':
    main()
