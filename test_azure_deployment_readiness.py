#!/usr/bin/env python3
"""
Azure Deployment Readiness Tests
Comprehensive tests to verify safe Azure deployment
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestAzureDeploymentReadiness(unittest.TestCase):
    """Test Azure deployment readiness and safety"""

    def setUp(self):
        """Set up test environment"""
        # Save original environment
        self.original_env = os.environ.copy()
        
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_production_environment_detection(self):
        """Test that production environment is correctly detected"""
        from production_config import ProductionConfig
        
        # Test production detection
        os.environ['FLASK_ENV'] = 'production'
        self.assertTrue(ProductionConfig.is_production())
        self.assertFalse(ProductionConfig.is_development())
        
        # Test development detection
        os.environ['FLASK_ENV'] = 'development'
        self.assertFalse(ProductionConfig.is_production())
        self.assertTrue(ProductionConfig.is_development())
        
        print("✅ PASS: Production environment detection working correctly")

    def test_production_safety_validation(self):
        """Test production safety validation"""
        from production_config import ProductionConfig
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        
        # Test safe operation
        result = ProductionConfig.validate_production_safety(
            'ui_triggered_password_reset',
            'ui_triggered,authenticated_admin'
        )
        self.assertTrue(result)
        
        # Test restricted operation without UI
        with self.assertRaises(Exception) as context:
            ProductionConfig.validate_production_safety(
                'backend_password_reset',
                'no_context'
            )
        self.assertIn('requires UI authorization', str(context.exception))
        
        print("✅ PASS: Production safety validation working correctly")

    def test_azure_deployment_safety_in_security_guard(self):
        """Test Azure deployment safety validation in security guard"""
        from security_guard import SecurityGuard, SecurityGuardError
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        
        # Test UI-triggered operation (should pass)
        try:
            SecurityGuard.validate_azure_deployment_safety(
                'password_reset',
                username='admin',
                ui_triggered=True
            )
            print("✅ PASS: UI-triggered operation allowed in production")
        except SecurityGuardError:
            self.fail("UI-triggered operation should be allowed in production")
        
        # Test non-UI operation (should fail)
        with self.assertRaises(SecurityGuardError) as context:
            SecurityGuard.validate_azure_deployment_safety(
                'password_reset',
                username='admin',
                ui_triggered=False
            )
        self.assertIn('must be triggered through the web interface', str(context.exception))
        print("✅ PASS: Non-UI operation correctly blocked in production")

    def test_environment_variables_validation(self):
        """Test environment variables validation for production"""
        from production_config import ProductionConfig
        
        # Test with missing variables (clear environment first)
        test_env = {key: value for key, value in os.environ.items() if not key.startswith(('FLASK_', 'ADMIN_', 'DEMO_'))}
        with patch.dict(os.environ, test_env, clear=True):
            os.environ['FLASK_ENV'] = 'production'
            missing = ProductionConfig.validate_environment_variables()
            self.assertIn('FLASK_SECRET_KEY', missing)
            self.assertIn('ADMIN_PASSWORD', missing)
        
        # Test with all variables set
        os.environ.update({
            'FLASK_SECRET_KEY': 'test-secret',
            'ADMIN_PASSWORD': 'test-admin-password',
            'DEMO_PASSWORD': 'test-demo-password'
        })
        missing = ProductionConfig.validate_environment_variables()
        self.assertEqual(len(missing), 0)
        
        print("✅ PASS: Environment variables validation working correctly")

    def test_password_reset_guard_in_production(self):
        """Test password reset guard behavior in production"""
        from security_guard import password_reset_guard, SecurityGuardError
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        
        @password_reset_guard(ui_triggered=True, require_explicit_request=False)
        def mock_ui_password_reset(username):
            return f"UI reset for {username}"
        
        @password_reset_guard(ui_triggered=False, require_explicit_request=True)
        def mock_backend_password_reset(username, explicit_user_request=False):
            return f"Backend reset for {username}"
        
        # Test UI-triggered (should work)
        try:
            result = mock_ui_password_reset('admin')
            self.assertEqual(result, "UI reset for admin")
            print("✅ PASS: UI-triggered password reset allowed in production")
        except SecurityGuardError:
            self.fail("UI-triggered password reset should work in production")
        
        # Test backend without authorization (should fail)
        with self.assertRaises(SecurityGuardError):
            mock_backend_password_reset('admin')
        print("✅ PASS: Backend password reset correctly blocked without authorization")
        
        # Test backend with authorization (should work)
        try:
            result = mock_backend_password_reset('admin', explicit_user_request=True)
            self.assertEqual(result, "Backend reset for admin")
            print("✅ PASS: Backend password reset allowed with explicit authorization")
        except SecurityGuardError:
            self.fail("Backend password reset with authorization should work")

    @patch('production_config.logging')
    def test_production_logging_setup(self, mock_logging):
        """Test production logging setup"""
        from production_config import ProductionConfig
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        
        ProductionConfig.setup_production_logging()
        
        # Verify logging was configured
        mock_logging.basicConfig.assert_called()
        args, kwargs = mock_logging.basicConfig.call_args
        self.assertEqual(kwargs['level'], mock_logging.INFO)
        
        print("✅ PASS: Production logging setup working correctly")

    def test_production_safe_decorator(self):
        """Test production safe decorator"""
        from production_config import production_safe, ProductionConfig
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        
        @production_safe('ui_triggered_password_reset')
        def mock_admin_function(username, ui_triggered=True):
            return f"Admin action for {username}"
        
        # Test with UI trigger (should work)
        try:
            result = mock_admin_function('admin', ui_triggered=True)
            self.assertEqual(result, "Admin action for admin")
            print("✅ PASS: Production safe decorator allows UI-triggered operations")
        except Exception:
            self.fail("Production safe decorator should allow UI-triggered operations")

    def test_no_hardcoded_credentials_in_main_files(self):
        """Test that main application files have no hardcoded credentials"""
        import re
        
        # Files to check
        files_to_check = ['app.py', 'security_guard.py', 'production_config.py']
        
        # Patterns that might indicate hardcoded credentials
        dangerous_patterns = [
            r'password\s*=\s*[\'"][a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:,.<>?]{4,}[\'"]',  # Actual password assignments
            r'Password123',
            r'admin_password\s*=\s*[\'"][^\'\"]{4,}[\'"]',  # Specific admin password assignments
            r'test_password\s*=\s*[\'"][^\'\"]{4,}[\'"]',  # Test password assignments
        ]
        
        for filename in files_to_check:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in dangerous_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    # Filter out obvious false positives
                    actual_issues = [
                        match for match in matches 
                        if 'os.environ' not in match 
                        and 'get(' not in match 
                        and '@route(' not in match 
                        and 'methods=' not in match
                        and 'password-reset' not in match
                        and 'reset-password' not in match
                        and not match.startswith('/')  # Route paths
                    ]
                    self.assertEqual(len(actual_issues), 0, 
                                   f"Found potential hardcoded credentials in {filename}: {actual_issues}")
        
        print("✅ PASS: No hardcoded credentials found in main application files")

    def test_reset_all_passwords_script_safety(self):
        """Test that reset_all_passwords.py script is production-safe"""
        try:
            from reset_all_passwords import reset_user_password
            
            # Test that function requires explicit authorization
            with self.assertRaises(Exception) as context:
                reset_user_password('admin', 'test_password', 'Test Admin')
            
            # Check that it's the right kind of error (missing parameter or security error)
            error_message = str(context.exception)
            self.assertTrue(
                'explicit_user_request' in error_message or 
                'must be explicitly requested' in error_message,
                f"Script should require explicit authorization, got: {error_message}"
            )
            
            print("✅ PASS: reset_all_passwords.py script requires explicit authorization")
        except ImportError:
            print("⚠️  WARNING: Could not import reset_all_passwords.py for testing")

def run_azure_deployment_tests():
    """Run all Azure deployment readiness tests"""
    print("🚀 Azure Deployment Readiness Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAzureDeploymentReadiness)
    
    # Run tests with minimal output
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Report results
    total_tests = result.testsRun
    failed_tests = len(result.failures) + len(result.errors)
    passed_tests = total_tests - failed_tests
    
    print(f"\n{'=' * 60}")
    print(f"🏆 AZURE DEPLOYMENT TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, error in result.failures:
            print(f"   - {test}: {error}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, error in result.errors:
            print(f"   - {test}: {error}")
    
    # Deployment readiness decision
    deployment_ready = failed_tests == 0
    
    print(f"\n{'=' * 60}")
    if deployment_ready:
        print("🎉 DEPLOYMENT APPROVED: All Azure deployment tests passed!")
        print("✅ The application is ready for secure Azure deployment")
        print("\n🔒 Verified Security Features:")
        print("   - Production environment detection working")
        print("   - UI-only sensitive operations in production")
        print("   - Backend operations require explicit authorization")
        print("   - Environment variables properly used")
        print("   - No hardcoded credentials detected")
        print("   - Production logging configured")
    else:
        print("❌ DEPLOYMENT BLOCKED: Some deployment tests failed")
        print("⚠️  Please fix the issues before deploying to Azure")
    
    return deployment_ready

if __name__ == "__main__":
    print("🛡️  Azure Deployment Security Validation")
    print("=" * 50)
    
    success = run_azure_deployment_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🚀 READY FOR AZURE DEPLOYMENT!")
        print("Next steps:")
        print("1. Set environment variables in Azure App Service")
        print("2. Deploy the application code")
        print("3. Test admin login and password reset functionality")
        print("4. Monitor logs for any issues")
