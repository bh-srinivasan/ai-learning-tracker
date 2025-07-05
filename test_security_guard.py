#!/usr/bin/env python3
"""
Security Guard Test Suite
Verifies that security guards prevent unsafe operations
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security_guard import (
    SecurityGuard, SecurityGuardError, security_guard,
    validate_test_environment, get_test_credentials
)

class TestSecurityGuard(unittest.TestCase):
    """Test security guard functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original environment
        self.original_env = os.environ.copy()
        
        # Set test environment
        os.environ['FLASK_ENV'] = 'development'
        os.environ['ADMIN_PASSWORD'] = 'test_admin_password'
        os.environ['DEMO_PASSWORD'] = 'test_demo_password'
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_development_environment_detection(self):
        """Test that development environment is correctly detected"""
        os.environ['FLASK_ENV'] = 'development'
        self.assertTrue(SecurityGuard.is_development())
        
        os.environ['NODE_ENV'] = 'development'
        self.assertTrue(SecurityGuard.is_development())
        
        os.environ['FLASK_ENV'] = 'production'
        os.environ.pop('NODE_ENV', None)
        self.assertFalse(SecurityGuard.is_development())
    
    def test_test_user_validation(self):
        """Test that only allowed test users are recognized"""
        self.assertTrue(SecurityGuard.is_test_user('admin'))
        self.assertTrue(SecurityGuard.is_test_user('demo'))
        self.assertFalse(SecurityGuard.is_test_user('bharath'))
        self.assertFalse(SecurityGuard.is_test_user('random_user'))
    
    def test_operation_validation_in_development(self):
        """Test operation validation in development environment"""
        os.environ['FLASK_ENV'] = 'development'
        
        # Should allow operations on test users
        self.assertTrue(SecurityGuard.validate_operation('password_reset', 'admin'))
        self.assertTrue(SecurityGuard.validate_operation('password_reset', 'demo'))
        
        # Should block operations on non-test users
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.validate_operation('password_reset', 'bharath')
    
    def test_operation_validation_in_production(self):
        """Test that operations are blocked in production"""
        os.environ['FLASK_ENV'] = 'production'
        
        # Should block all dangerous operations in production
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.validate_operation('password_reset', 'admin')
        
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.validate_operation('user_delete', 'demo')
    
    def test_force_override(self):
        """Test force override functionality"""
        os.environ['FLASK_ENV'] = 'production'
        
        # Should allow operations with force=True
        self.assertTrue(SecurityGuard.validate_operation('password_reset', 'admin', force=True))
    
    def test_security_guard_decorator(self):
        """Test security guard decorator"""
        
        @security_guard('password_reset', username_param=0)  # Username is first parameter
        def test_function(username):
            return f"Password reset for {username}"
        
        # Should work in development with test users
        os.environ['FLASK_ENV'] = 'development'
        result = test_function('admin')
        self.assertEqual(result, "Password reset for admin")
        
        # Should block non-test users in development
        with self.assertRaises(SecurityGuardError):
            test_function('bharath')
        
        # Should block everything in production
        os.environ['FLASK_ENV'] = 'production'
        with self.assertRaises(SecurityGuardError):
            test_function('admin')
    
    def test_validate_test_environment(self):
        """Test test environment validation"""
        os.environ['FLASK_ENV'] = 'development'
        os.environ['ADMIN_PASSWORD'] = 'test_password'
        os.environ['DEMO_PASSWORD'] = 'test_password'
        
        # Should pass with proper environment
        self.assertTrue(validate_test_environment())
        
        # Should fail in production
        os.environ['FLASK_ENV'] = 'production'
        with self.assertRaises(SecurityGuardError):
            validate_test_environment()
        
        # Should fail with missing environment variables
        os.environ['FLASK_ENV'] = 'development'
        del os.environ['ADMIN_PASSWORD']
        with self.assertRaises(SecurityGuardError):
            validate_test_environment()
    
    def test_get_test_credentials(self):
        """Test getting test credentials from environment"""
        os.environ['ADMIN_PASSWORD'] = 'test_admin_123'
        os.environ['DEMO_PASSWORD'] = 'test_demo_456'
        
        creds = get_test_credentials()
        
        self.assertEqual(creds['admin']['username'], 'admin')
        self.assertEqual(creds['admin']['password'], 'test_admin_123')
        self.assertEqual(creds['demo']['username'], 'demo')
        self.assertEqual(creds['demo']['password'], 'test_demo_456')
    
    def test_ui_interaction_requirement(self):
        """Test UI interaction requirement"""
        # Without automation flag, should pass
        self.assertTrue(SecurityGuard.require_ui_interaction())
        
        # With automation flag, should fail
        os.environ['AUTOMATED_EXECUTION'] = 'true'
        with self.assertRaises(SecurityGuardError):
            SecurityGuard.require_ui_interaction()

class TestSecurityGuardIntegration(unittest.TestCase):
    """Integration tests for security guard"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.original_env = os.environ.copy()
        os.environ['FLASK_ENV'] = 'development'
        os.environ['ADMIN_PASSWORD'] = 'test_admin_password'
        os.environ['DEMO_PASSWORD'] = 'test_demo_password'
    
    def tearDown(self):
        """Restore environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_password_reset_protection(self):
        """Test that password reset operations are properly protected"""
        
        @security_guard('password_reset', username_param=0, require_ui=False)
        def mock_password_reset(username, password):
            return f"Reset password for {username}"
        
        # Should work for allowed users
        result = mock_password_reset('admin', 'new_password')
        self.assertEqual(result, "Reset password for admin")
        
        result = mock_password_reset('demo', 'new_password')
        self.assertEqual(result, "Reset password for demo")
        
        # Should block disallowed users
        with self.assertRaises(SecurityGuardError):
            mock_password_reset('bharath', 'new_password')
    
    def test_user_deletion_protection(self):
        """Test that user deletion operations are properly protected"""
        
        @security_guard('user_delete', username_param=0, require_ui=True)
        def mock_user_delete(username):
            return f"Deleted user {username}"
        
        # Should work for allowed users (when UI interaction is mocked)
        with patch.object(SecurityGuard, 'require_ui_interaction', return_value=True):
            result = mock_user_delete('demo')
            self.assertEqual(result, "Deleted user demo")
        
        # Should block disallowed users
        with self.assertRaises(SecurityGuardError):
            mock_user_delete('bharath')

def run_security_tests():
    """Run all security guard tests"""
    print("🛡️  Running Security Guard Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityGuard))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityGuardIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All security guard tests passed!")
        print("🔒 Security safeguards are working correctly")
    else:
        print("❌ Some security guard tests failed!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)
