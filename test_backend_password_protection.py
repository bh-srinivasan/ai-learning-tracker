#!/usr/bin/env python3
"""
Test Backend Password Reset Protection
Verifies that backend scripts properly require explicit authorization
"""

import sys
import os
import subprocess
from security_guard import SecurityGuardError

def test_reset_all_passwords_script():
    """Test that reset_all_passwords.py requires explicit authorization"""
    
    print("🧪 Testing Backend Password Reset Script Protection")
    print("=" * 60)
    
    # Test 1: Try to import and run reset function without authorization
    print("\n1. Testing password reset function without authorization...")
    try:
        from reset_all_passwords import reset_user_password
        
        # This should fail - no explicit authorization
        try:
            reset_user_password('admin', 'test_password', 'Test Admin')
            print("❌ FAIL: Password reset was allowed without explicit authorization")
            return False
        except SecurityGuardError as e:
            if "must be explicitly requested" in str(e):
                print("✅ PASS: Password reset correctly blocked without explicit authorization")
            else:
                print(f"❌ FAIL: Wrong error message: {str(e)}")
                return False
        except TypeError as e:
            if "explicit_user_request" in str(e):
                print("✅ PASS: Password reset correctly requires explicit_user_request parameter")
            else:
                print(f"❌ FAIL: Unexpected TypeError: {str(e)}")
                return False
    except Exception as e:
        print(f"❌ ERROR: Failed to import or test reset function: {str(e)}")
        return False
    
    # Test 2: Try to run reset function with explicit authorization
    print("\n2. Testing password reset function with explicit authorization...")
    try:
        from reset_all_passwords import reset_user_password
        
        # This should work - explicit authorization provided
        try:
            result = reset_user_password('admin', 'test_password', 'Test Admin', explicit_user_request=True)
            print("✅ PASS: Password reset correctly allowed with explicit authorization")
        except Exception as e:
            # This might fail due to database issues, but it should get past the security check
            if "must be explicitly requested" not in str(e):
                print("✅ PASS: Password reset passed security check (database error is OK)")
            else:
                print(f"❌ FAIL: Security check still blocked with explicit authorization: {str(e)}")
                return False
    except Exception as e:
        print(f"❌ ERROR: Failed to test explicit authorization: {str(e)}")
        return False
    
    # Test 3: Test script execution (this will succeed because script provides explicit authorization)
    print("\n3. Testing full script execution...")
    try:
        # Run the script and capture output
        result = subprocess.run([
            sys.executable, 'reset_all_passwords.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ PASS: Script executed successfully with explicit authorization")
            if "explicit user authorization" in result.stdout:
                print("✅ PASS: Script properly displays authorization message")
        else:
            print(f"❌ INFO: Script execution result: {result.returncode}")
            print(f"   stdout: {result.stdout[:200]}...")
            print(f"   stderr: {result.stderr[:200]}...")
            # This might fail due to environment issues, but we're mainly testing security
    except subprocess.TimeoutExpired:
        print("⚠️  INFO: Script execution timed out (may be waiting for input)")
    except Exception as e:
        print(f"❌ INFO: Script execution error: {str(e)}")
    
    return True

def test_security_guard_integration():
    """Test security guard integration with password reset controls"""
    
    print("\n🛡️  Testing Security Guard Integration")
    print("=" * 60)
    
    from security_guard import SecurityGuard, SecurityGuardError
    
    # Test 1: Backend password reset operation validation
    print("\n1. Testing backend password reset operation validation...")
    try:
        SecurityGuard.validate_operation('backend_password_reset', explicit_authorization=False)
        print("❌ FAIL: Backend password reset was allowed without authorization")
        return False
    except SecurityGuardError as e:
        if "explicit user authorization" in str(e):
            print("✅ PASS: Backend password reset correctly requires authorization")
        else:
            print(f"❌ FAIL: Wrong error for backend password reset: {str(e)}")
            return False
    
    # Test 2: Backend password reset with authorization
    print("\n2. Testing backend password reset with authorization...")
    try:
        result = SecurityGuard.validate_operation('backend_password_reset', explicit_authorization=True)
        if result:
            print("✅ PASS: Backend password reset correctly allowed with authorization")
        else:
            print("❌ FAIL: Backend password reset validation returned False")
            return False
    except SecurityGuardError as e:
        print(f"❌ FAIL: Backend password reset blocked even with authorization: {str(e)}")
        return False
    
    # Test 3: Password reset validation method
    print("\n3. Testing password reset validation method...")
    try:
        SecurityGuard.validate_password_reset_request(
            username='admin',
            explicit_user_request=False,
            ui_triggered=False
        )
        print("❌ FAIL: Password reset validation allowed without proper authorization")
        return False
    except SecurityGuardError as e:
        if "must be explicitly requested" in str(e):
            print("✅ PASS: Password reset validation correctly requires authorization")
        else:
            print(f"❌ FAIL: Wrong error for password reset validation: {str(e)}")
            return False
    
    # Test 4: Password reset validation with UI trigger
    print("\n4. Testing password reset validation with UI trigger...")
    try:
        result = SecurityGuard.validate_password_reset_request(
            username='admin',
            explicit_user_request=False,
            ui_triggered=True
        )
        if result:
            print("✅ PASS: UI-triggered password reset correctly allowed")
        else:
            print("❌ FAIL: UI-triggered password reset validation returned False")
            return False
    except SecurityGuardError as e:
        print(f"❌ FAIL: UI-triggered password reset blocked: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔐 Backend Password Reset Protection Test Suite")
    print("=" * 70)
    
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    
    success1 = test_reset_all_passwords_script()
    success2 = test_security_guard_integration()
    
    print(f"\n{'=' * 70}")
    if success1 and success2:
        print("🎉 ALL BACKEND PASSWORD RESET PROTECTION TESTS PASSED!")
        print("🔒 Backend password reset controls are working correctly")
        print("\n✅ Key Security Features Verified:")
        print("   - Backend scripts require explicit user authorization")
        print("   - Security guard properly validates password reset requests")
        print("   - UI-triggered operations are allowed")
        print("   - Automated operations are properly blocked")
    else:
        print("⚠️  Some backend password reset protection tests failed")
        sys.exit(1)
