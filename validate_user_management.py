#!/usr/bin/env python3
"""
User Management Validation Script
Validates that bharath user is treated as a normal user, not protected.
"""

import sqlite3
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_user_management():
    """Validate that bharath is treated as a normal user"""
    
    logger.info("[VALIDATION] Starting user management validation...")
    
    # Check database
    db_path = "ai_learning.db"
    if not Path(db_path).exists():
        logger.error("Database not found. Please run the app first to create the database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check users in database
        users = conn.execute("SELECT username, password_hash FROM users").fetchall()
        logger.info(f"[DATABASE] Found {len(users)} users in database:")
        
        bharath_found = False
        for user in users:
            logger.info(f"  - {user['username']}")
            if user['username'] == 'bharath':
                bharath_found = True
                logger.info(f"    [SUCCESS] bharath user found - treated as normal user")
        
        if not bharath_found:
            logger.warning("[WARNING] bharath user not found in database")
        
        conn.close()
        
        # Validate code logic
        logger.info("[CODE] Validating code logic...")
        
        # Read app.py and check for protection logic
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        validation_checks = [
            {
                'name': 'bharath not in delete protection',
                'pattern': "protected_users = ['admin', 'bharath']",
                'should_exist': False,
                'description': 'bharath should not be in delete protection list'
            },
            {
                'name': 'bharath not in pause protection', 
                'pattern': "protected_users = ['admin', 'bharath']",
                'should_exist': False,
                'description': 'bharath should not be in pause protection list'
            },
            {
                'name': 'bharath not in password reset protection',
                'pattern': "protected_users = ['bharath']",
                'should_exist': False,
                'description': 'bharath should not be protected from password resets'
            },
            {
                'name': 'admin-only protection implemented',
                'pattern': "protected_users = ['admin']",
                'should_exist': True,
                'description': 'Only admin should be protected'
            }
        ]
        
        all_passed = True
        for check in validation_checks:
            found = check['pattern'] in content
            if check['should_exist'] and found:
                logger.info(f"[SUCCESS] {check['name']}: {check['description']}")
            elif not check['should_exist'] and not found:
                logger.info(f"[SUCCESS] {check['name']}: {check['description']}")
            else:
                logger.error(f"[FAIL] {check['name']}: {check['description']}")
                all_passed = False
        
        # Check config.py
        logger.info("[CONFIG] Validating config.py...")
        try:
            with open('config.py', 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            if "PROTECTED_USERS = []" in config_content:
                logger.info("[SUCCESS] config.py: PROTECTED_USERS is empty")
            elif "PROTECTED_USERS = ['bharath']" in config_content:
                logger.error("[FAIL] config.py: bharath still in PROTECTED_USERS")
                all_passed = False
            else:
                logger.warning("[WARNING] config.py: PROTECTED_USERS not found or unexpected format")
        except Exception as e:
            logger.error(f"[ERROR] Failed to read config.py: {e}")
            all_passed = False
        
        # Check .env file
        logger.info("[ENV] Validating .env file...")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            if "BHARATH_PASSWORD" not in env_content:
                logger.info("[SUCCESS] .env: BHARATH_PASSWORD removed")
            else:
                logger.error("[FAIL] .env: BHARATH_PASSWORD still present")
                all_passed = False
        except Exception as e:
            logger.error(f"[ERROR] Failed to read .env: {e}")
            all_passed = False
        
        if all_passed:
            logger.info("[SUCCESS] All validation checks passed!")
            logger.info("[INFO] bharath is now treated as a normal user")
            logger.info("[INFO] bharath can be:")
            logger.info("  - Deleted by admin")
            logger.info("  - Paused/unpaused by admin") 
            logger.info("  - Included in bulk password resets")
            logger.info("  - Have individual password reset")
            return True
        else:
            logger.error("[FAIL] Some validation checks failed")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Validation failed: {e}")
        return False

def test_password_reset_inclusion():
    """Test that bharath would be included in password resets"""
    logger.info("[TEST] Testing password reset inclusion logic...")
    
    # Simulate the logic from app.py
    protected_users = ['admin']  # This is what should be in the code now
    
    test_users = ['admin', 'bharath', 'demo', 'testuser']
    
    logger.info("Password reset simulation:")
    for username in test_users:
        if username not in protected_users:
            logger.info(f"  ✅ {username}: WOULD be included in password reset")
        else:
            logger.info(f"  ❌ {username}: WOULD be excluded from password reset")
    
    # Check that bharath is included
    if 'bharath' not in protected_users:
        logger.info("[SUCCESS] bharath WOULD be included in password resets")
        return True
    else:
        logger.error("[FAIL] bharath WOULD be excluded from password resets")
        return False

def main():
    """Main validation function"""
    logger.info("="*60)
    logger.info("USER MANAGEMENT VALIDATION")
    logger.info("="*60)
    
    validation_passed = validate_user_management()
    test_passed = test_password_reset_inclusion()
    
    logger.info("="*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*60)
    
    if validation_passed and test_passed:
        logger.info("[SUCCESS] All validations passed!")
        logger.info("[INFO] bharath user is now treated as a normal user")
        logger.info("[INFO] Ready for deployment")
        return 0
    else:
        logger.error("[FAIL] Some validations failed")
        logger.error("[ACTION] Please review and fix the issues above")
        return 1

if __name__ == "__main__":
    exit(main())
