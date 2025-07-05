#!/usr/bin/env python3
"""
Unit tests to verify password reset validation logic
"""

import sqlite3
import tempfile
import os
import sys
import unittest
from werkzeug.security import generate_password_hash, check_password_hash

# Add the project directory to the path so we can import from reset_all_passwords
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestPasswordResetValidation(unittest.TestCase):
    """Test password reset validation and restrictions"""
    
    def setUp(self):
        """Set up test database"""
        # Create temporary database for testing
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_path = self.test_db.name
        self.test_db.close()
        
        # Create test database with users
        conn = sqlite3.connect(self.test_db_path)
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test users
        test_users = [
            ('admin', generate_password_hash('admin_password')),
            ('demo', generate_password_hash('demo_password')),
            ('bharath', generate_password_hash('bharath_password')),
            ('john', generate_password_hash('john_password')),
            ('testuser', generate_password_hash('test_password'))
        ]
        
        for username, password_hash in test_users:
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
        
        conn.commit()
        conn.close()
        
        # Mock the original database path
        self.original_db_path = 'ai_learning.db'
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def test_demo_user_password_reset_allowed(self):
        """Test that demo user password reset is allowed"""
        from reset_all_passwords import reset_user_password
        
        # Temporarily replace database path
        import reset_all_passwords
        original_connect = sqlite3.connect
        
        def mock_connect(db_path):
            return original_connect(self.test_db_path)
        
        sqlite3.connect = mock_connect
        
        try:
            result = reset_user_password('demo', 'new_password', 'Demo User')
            self.assertTrue(result, "Demo user password reset should be allowed")
            
            # Verify password was actually changed
            conn = sqlite3.connect(self.test_db_path)
            user = conn.execute('SELECT password_hash FROM users WHERE username = ?', ('demo',)).fetchone()
            conn.close()
            
            self.assertTrue(check_password_hash(user[0], 'new_password'), "Password should be updated")
            
        finally:
            sqlite3.connect = original_connect
    
    def test_admin_user_password_reset_allowed(self):
        """Test that admin user password reset is allowed"""
        from reset_all_passwords import reset_user_password
        
        # Temporarily replace database path
        import reset_all_passwords
        original_connect = sqlite3.connect
        
        def mock_connect(db_path):
            return original_connect(self.test_db_path)
        
        sqlite3.connect = mock_connect
        
        try:
            result = reset_user_password('admin', 'new_admin_password', 'Admin User')
            self.assertTrue(result, "Admin user password reset should be allowed")
            
        finally:
            sqlite3.connect = original_connect
    
    def test_bharath_user_password_reset_blocked(self):
        """Test that bharath user password reset is blocked"""
        from reset_all_passwords import reset_user_password
        
        # Temporarily replace database path
        import reset_all_passwords
        original_connect = sqlite3.connect
        
        def mock_connect(db_path):
            return original_connect(self.test_db_path)
        
        sqlite3.connect = mock_connect
        
        try:
            result = reset_user_password('bharath', 'new_password', 'Bharath User')
            self.assertFalse(result, "Bharath user password reset should be blocked")
            
            # Verify password was NOT changed
            conn = sqlite3.connect(self.test_db_path)
            user = conn.execute('SELECT password_hash FROM users WHERE username = ?', ('bharath',)).fetchone()
            conn.close()
            
            self.assertTrue(check_password_hash(user[0], 'bharath_password'), "Password should remain unchanged")
            
        finally:
            sqlite3.connect = original_connect
    
    def test_other_users_password_reset_blocked(self):
        """Test that other users' password resets are blocked"""
        from reset_all_passwords import reset_user_password
        
        # Temporarily replace database path
        import reset_all_passwords
        original_connect = sqlite3.connect
        
        def mock_connect(db_path):
            return original_connect(self.test_db_path)
        
        sqlite3.connect = mock_connect
        
        try:
            # Test john user
            result = reset_user_password('john', 'new_password', 'John User')
            self.assertFalse(result, "John user password reset should be blocked")
            
            # Test testuser
            result = reset_user_password('testuser', 'new_password', 'Test User')
            self.assertFalse(result, "Test user password reset should be blocked")
            
        finally:
            sqlite3.connect = original_connect
    
    def test_nonexistent_user_password_reset(self):
        """Test password reset for non-existent user"""
        from reset_all_passwords import reset_user_password
        
        # Temporarily replace database path
        import reset_all_passwords
        original_connect = sqlite3.connect
        
        def mock_connect(db_path):
            return original_connect(self.test_db_path)
        
        sqlite3.connect = mock_connect
        
        try:
            result = reset_user_password('nonexistent', 'new_password', 'Non-existent User')
            self.assertFalse(result, "Non-existent user password reset should fail")
            
        finally:
            sqlite3.connect = original_connect

def run_password_reset_tests():
    """Run all password reset validation tests"""
    print("🧪 Running Password Reset Validation Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPasswordResetValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All password reset validation tests passed!")
        print("🔒 Password reset restrictions are working correctly")
    else:
        print("❌ Some password reset validation tests failed!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_password_reset_tests()
    sys.exit(0 if success else 1)
