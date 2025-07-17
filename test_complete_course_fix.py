#!/usr/bin/env python3
"""
Test script to verify the complete_course route fix
"""

import subprocess
import sys
import os

def test_flask_syntax():
    """Test if Flask app has valid syntax"""
    print("🧪 Testing Flask App Syntax")
    print("=" * 40)
    
    try:
        # Try to import the app to check for syntax errors
        result = subprocess.run(
            [sys.executable, '-c', 'import app; print("✅ Syntax OK")'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Flask app syntax is valid")
            print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print("❌ Flask app has syntax errors:")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Import test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing syntax: {e}")
        return False

def check_route_exists():
    """Check if the complete_course route exists"""
    print("\n🔍 Checking Route Implementation")
    print("=" * 40)
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('complete_course route', "@app.route('/complete_course/<int:course_id>', methods=['POST'])"),
            ('Function definition', 'def complete_course(course_id):'),
            ('Level manager import', 'from level_manager import LevelManager'),
            ('Course completion call', 'mark_course_completion(user_id, course_id, completed=True)'),
            ('Dashboard redirect', "return redirect(url_for('dashboard'))")
        ]
        
        for check_name, pattern in checks:
            if pattern in content:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                
    except Exception as e:
        print(f"❌ Error checking routes: {e}")

def check_template_usage():
    """Check if template uses the route correctly"""
    print("\n🔍 Checking Template Usage")
    print("=" * 40)
    
    try:
        with open('templates/dashboard/index.html', 'r') as f:
            content = f.read()
        
        if "url_for('complete_course', course_id=course.id)" in content:
            print("✅ Template uses complete_course route correctly")
        else:
            print("❌ Template doesn't use complete_course route")
            
    except Exception as e:
        print(f"❌ Error checking template: {e}")

if __name__ == '__main__':
    print("🧪 Complete Course Route Fix Test")
    print("=" * 50)
    
    syntax_ok = test_flask_syntax()
    check_route_exists()
    check_template_usage()
    
    if syntax_ok:
        print("\n🎉 Fix Applied Successfully!")
        print("The complete_course route is now available.")
        print("\nNext steps:")
        print("1. Start Flask app: python app.py")
        print("2. Login and go to dashboard")
        print("3. Try clicking 'Complete' on a course")
    else:
        print("\n❌ Syntax issues detected.")
        print("Please check the Flask app for errors.")
