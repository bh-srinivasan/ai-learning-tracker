#!/usr/bin/env python3
"""
Test Controlled Password Reset Behavior
Verifies that password resets follow the new security model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from security_guard import SecurityGuard, SecurityGuardError, password_reset_guard
import unittest
from unittest.mock import patch, MagicMock

class TestControlledPasswordReset(unittest.TestCase):
    """Test the controlled password reset behavior"""

    def setUp(self):
        """Set up test environment"""
        os.environ['FLASK_ENV'] = 'development'
        
    def test_backend_password_reset_blocked_without_authorization(self):
        """Test that backend password resets are blocked without explicit authorization"""
        
        @password_reset_guard(ui_triggered=False, require_explicit_request=True)
        def mock_backend_reset(username, password):
            return f"Password reset for {username}"
        
        # Should be blocked without explicit authorization
        with self.assertRaises(SecurityGuardError) as context:
            mock_backend_reset('admin', 'new_password')
        
        self.assertIn("Password reset must be explicitly requested", str(context.exception))
        print("✅ PASS: Backend password reset correctly blocked without authorization")
    
    def test_backend_password_reset_allowed_with_authorization(self):
        """Test that backend password resets are allowed with explicit authorization"""
        
        @password_reset_guard(ui_triggered=False, require_explicit_request=True)
        def mock_backend_reset(username, password, explicit_user_request=False):
            return f"Password reset for {username}"
        
        # Should be allowed with explicit authorization
        try:
            result = mock_backend_reset('admin', 'new_password', explicit_user_request=True)
            self.assertEqual(result, "Password reset for admin")
            print("✅ PASS: Backend password reset correctly allowed with explicit authorization")
        except SecurityGuardError as e:
            self.fail(f"Password reset should have been allowed with explicit authorization: {str(e)}")
    
    def test_ui_triggered_password_reset_allowed(self):
        """Test that UI-triggered password resets are allowed"""
        
        @password_reset_guard(ui_triggered=True, require_explicit_request=False)
        def mock_ui_reset(username, password):
            return f"UI password reset for {username}"
        
        # Should be allowed for UI-triggered operations
        try:
            result = mock_ui_reset('admin', 'new_password')
            self.assertEqual(result, "UI password reset for admin")
            print("✅ PASS: UI-triggered password reset correctly allowed")
        except SecurityGuardError as e:
            self.fail(f"UI-triggered password reset should have been allowed: {str(e)}")
    
    def test_password_reset_validation_logic(self):
        """Test the core password reset validation logic"""
        
        # Test 1: Backend without authorization - should fail
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.validate_password_reset_request(
                username='admin',
                explicit_user_request=False,
                ui_triggered=False
            )
        print("✅ PASS: Backend reset without authorization correctly blocked")
        
        # Test 2: Backend with authorization - should pass
        try:
            result = SecurityGuard.validate_password_reset_request(
                username='admin',
                explicit_user_request=True,
                ui_triggered=False
            )
            self.assertTrue(result)
            print("✅ PASS: Backend reset with authorization correctly allowed")
        except SecurityGuardError as e:
            self.fail(f"Backend reset with authorization should have been allowed: {str(e)}")
        
        # Test 3: UI-triggered - should pass
        try:
            result = SecurityGuard.validate_password_reset_request(
                username='admin',
                explicit_user_request=False,
                ui_triggered=True
            )
            self.assertTrue(result)
            print("✅ PASS: UI-triggered reset correctly allowed")
        except SecurityGuardError as e:
            self.fail(f"UI-triggered reset should have been allowed: {str(e)}")
    
    def test_authorization_required_operations(self):
        """Test that backend password resets are in authorization required operations"""
        self.assertIn('backend_password_reset', SecurityGuard.AUTHORIZATION_REQUIRED_OPERATIONS)
        self.assertIn('automated_password_reset', SecurityGuard.AUTHORIZATION_REQUIRED_OPERATIONS)
        print("✅ PASS: Backend password reset operations correctly require authorization")
    
    def test_ui_only_operations(self):
        """Test that admin operations are UI-only"""
        self.assertIn('admin_password_reset', SecurityGuard.UI_ONLY_OPERATIONS)
        self.assertIn('bulk_password_reset', SecurityGuard.UI_ONLY_OPERATIONS)
        self.assertIn('individual_password_reset', SecurityGuard.UI_ONLY_OPERATIONS)
        print("✅ PASS: Admin password reset operations correctly require UI")
    
    @patch.dict(os.environ, {'AUTOMATED_EXECUTION': 'true'})
    def test_automated_execution_blocked(self):
        """Test that automated execution is blocked"""
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.require_ui_interaction()
        print("✅ PASS: Automated execution correctly blocked")
    
    def test_security_guard_operation_validation(self):
        """Test security guard operation validation for password resets"""
        
        # Test UI-only operation validation
        with patch.dict(os.environ, {'AUTOMATED_EXECUTION': 'true'}):
            with self.assertRaises(SecurityGuardError):
                SecurityGuard.validate_operation('admin_password_reset')
        print("✅ PASS: UI-only operation correctly blocked in automated context")
        
        # Test authorization required operation validation
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.validate_operation('backend_password_reset', explicit_authorization=False)
        print("✅ PASS: Authorization required operation correctly blocked without authorization")
        
        # Test authorization required operation with authorization
        try:
            result = SecurityGuard.validate_operation('backend_password_reset', explicit_authorization=True)
            self.assertTrue(result)
            print("✅ PASS: Authorization required operation correctly allowed with authorization")
        except SecurityGuardError as e:
            self.fail(f"Operation with authorization should have been allowed: {str(e)}")

def run_controlled_password_reset_tests():
    """Run all controlled password reset tests"""
    print("🧪 Testing Controlled Password Reset Behavior")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestControlledPasswordReset)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Report results
    total_tests = result.testsRun
    failed_tests = len(result.failures) + len(result.errors)
    passed_tests = total_tests - failed_tests
    
    print(f"\n{'=' * 60}")
    print(f"🏆 CONTROLLED PASSWORD RESET TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, error in result.failures:
            print(f"   - {test}: {error}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, error in result.errors:
            print(f"   - {test}: {error}")
    
    return failed_tests == 0

if __name__ == "__main__":
    print("🛡️  Controlled Password Reset Security Test Suite")
    print("=" * 60)
    
    success = run_controlled_password_reset_tests()
    
    print(f"\n{'=' * 60}")
    if success:
        print("🎉 ALL CONTROLLED PASSWORD RESET TESTS PASSED!")
        print("🔒 Password reset controls are working correctly")
        print("\n✅ Key Security Features Verified:")
        print("   - Backend password resets require explicit authorization")
        print("   - UI-triggered password resets are allowed for admins")
        print("   - Automated execution is properly blocked")
        print("   - Authorization controls are enforced")
    else:
        print("⚠️  Some controlled password reset tests failed")
        sys.exit(1)
