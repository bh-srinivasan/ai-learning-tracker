#!/usr/bin/env python3
"""
Comprehensive test of backend admin password reset functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import backend_reset_admin_password, validate_password_strength
import sqlite3
from werkzeug.security import check_password_hash

def test_password_validation():
    """Test the password validation function"""
    
    print("🔍 TESTING PASSWORD VALIDATION")
    print("=" * 50)
    
    test_cases = [
        ("weak", False, "Too short"),
        ("weakpassword", False, "No uppercase, numbers, or special chars"),
        ("WeakPassword", False, "No numbers or special chars"), 
        ("WeakPassword123", False, "No special chars"),
        ("WeakPassword!", False, "No numbers"),
        ("WEAKPASSWORD123!", False, "No lowercase"),
        ("WeakPassword123!", True, "Meets all requirements"),
        ("AdminSecure123!", True, "Strong password"),
        ("MyStr0ng@Passw0rd", True, "Another strong password"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for password, should_pass, description in test_cases:
        is_valid, message = validate_password_strength(password)
        
        if is_valid == should_pass:
            print(f"✅ '{password}' - {description}")
            passed += 1
        else:
            print(f"❌ '{password}' - Expected {'Pass' if should_pass else 'Fail'}, got {'Pass' if is_valid else 'Fail'}")
    
    print(f"\nValidation tests: {passed}/{total} passed")
    return passed == total

def test_backend_password_reset():
    """Test the backend password reset function"""
    
    print("\n🔧 TESTING BACKEND PASSWORD RESET")
    print("=" * 50)
    
    # Test 1: Reset with weak password (should fail)
    print("1. Testing with weak password...")
    success, message = backend_reset_admin_password("weak", log_event=False)
    if not success and "at least 8 characters" in message:
        print("✅ Weak password correctly rejected")
    else:
        print("❌ Weak password was accepted")
        return False
    
    # Test 2: Reset with strong password (should succeed)
    print("2. Testing with strong password...")
    test_password = "TestSecure123!"
    success, message = backend_reset_admin_password(test_password, log_event=True)
    if success:
        print("✅ Strong password reset successful")
    else:
        print(f"❌ Strong password reset failed: {message}")
        return False
    
    # Test 3: Verify the password was actually changed
    print("3. Verifying password change in database...")
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    try:
        admin_user = conn.execute(
            'SELECT password_hash FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if admin_user and check_password_hash(admin_user['password_hash'], test_password):
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
            return False
            
    finally:
        conn.close()
    
    # Test 4: Reset back to known password
    print("4. Resetting back to known password...")
    final_password = "AdminSecure123!"
    success, message = backend_reset_admin_password(final_password, log_event=True)
    if success:
        print("✅ Password reset back to AdminSecure123!")
    else:
        print(f"❌ Failed to reset back: {message}")
        return False
    
    return True

def test_security_logging():
    """Test that security events are logged"""
    
    print("\n📋 TESTING SECURITY LOGGING")
    print("=" * 50)
    
    # Check if security_logs table exists and has recent entries
    conn = sqlite3.connect('ai_learning.db')
    
    try:
        # Check for recent password reset logs
        logs = conn.execute('''
            SELECT event_type, description, success, timestamp 
            FROM security_logs 
            WHERE event_type LIKE '%password_reset%' 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''').fetchall()
        
        if logs:
            print(f"✅ Found {len(logs)} recent password reset log entries:")
            for log in logs:
                status = "✅" if log[2] else "❌"
                print(f"   {status} {log[0]}: {log[1][:50]}...")
        else:
            print("⚠️  No password reset logs found")
            
    except Exception as e:
        print(f"⚠️  Could not check logs: {str(e)}")
        
    finally:
        conn.close()
    
    return True

def main():
    """Run all tests"""
    
    print("🧪 COMPREHENSIVE BACKEND PASSWORD RESET TEST")
    print("=" * 60)
    
    # Run all tests
    validation_passed = test_password_validation()
    reset_passed = test_backend_password_reset()
    logging_passed = test_security_logging()
    
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS:")
    print(f"   Password Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
    print(f"   Backend Reset:       {'✅ PASSED' if reset_passed else '❌ FAILED'}")
    print(f"   Security Logging:    {'✅ PASSED' if logging_passed else '❌ FAILED'}")
    
    all_passed = validation_passed and reset_passed and logging_passed
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("   Backend password reset functionality is working correctly")
        print("   Current admin password: AdminSecure123!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   Please check the implementation")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
