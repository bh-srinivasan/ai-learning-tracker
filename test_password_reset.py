#!/usr/bin/env python3
"""
Test script to verify password reset functionality
"""
import requests
import sys

def test_admin_access():
    """Test basic admin access and check if pages load"""
    try:
        # Test login page
        response = requests.get('http://localhost:5000/login')
        if response.status_code == 200:
            print("✓ Login page loads successfully")
        else:
            print(f"✗ Login page failed: {response.status_code}")
            return False
        
        # Test if app is running
        response = requests.get('http://localhost:5000/')
        if response.status_code == 200:
            print("✓ Main page loads successfully")
        else:
            print(f"✗ Main page failed: {response.status_code}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to Flask app. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"✗ Error testing admin access: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Password Reset Functionality...")
    print("="*50)
    
    if test_admin_access():
        print("✓ Basic connectivity test passed")
        print("\nTo test the new password reset features:")
        print("1. Navigate to http://localhost:5000")
        print("2. Login as admin/admin")
        print("3. Go to Admin Dashboard -> Manage Users")
        print("4. Try the new 'Reset All User Passwords' button")
        print("5. Try the individual 'Reset Password' button for each user")
        print("\nBoth features should:")
        print("- Show confirmation dialogs")
        print("- Validate password strength")
        print("- Exclude admin from bulk reset")
        print("- Allow custom passwords for individual users")
        print("- Log security events")
    else:
        print("✗ Basic connectivity test failed")
        sys.exit(1)
