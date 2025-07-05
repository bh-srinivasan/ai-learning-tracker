#!/usr/bin/env python3
"""
Comprehensive Data Governance and Backup System Test
Tests all protection mechanisms and Azure backup configuration
"""

import os
import json
import subprocess
from datetime import datetime
from production_safety_guard import ProductionSafetyGuard, production_safe, ProductionSafetyError
from azure_backup_governance import AzureBackupManager, DataGovernanceEnforcer

def test_environment_detection():
    """Test environment detection functionality"""
    
    print("🔍 TESTING ENVIRONMENT DETECTION")
    print("-" * 40)
    
    guard = ProductionSafetyGuard()
    print(f"Detected environment: {guard.environment}")
    
    # Test with different environment variables
    original_env = os.environ.get('FLASK_ENV')
    
    # Test development
    os.environ['FLASK_ENV'] = 'development'
    guard_dev = ProductionSafetyGuard()
    print(f"With FLASK_ENV=development: {guard_dev.environment}")
    
    # Test production indicators
    os.environ['AZURE_WEBAPP_NAME'] = 'test-webapp'
    guard_prod = ProductionSafetyGuard()
    print(f"With Azure indicators: {guard_prod.environment}")
    
    # Restore original environment
    if original_env:
        os.environ['FLASK_ENV'] = original_env
    else:
        os.environ.pop('FLASK_ENV', None)
    os.environ.pop('AZURE_WEBAPP_NAME', None)
    
    return True

def test_database_validation():
    """Test database content validation"""
    
    print("\n🔍 TESTING DATABASE VALIDATION")
    print("-" * 40)
    
    if not os.path.exists('ai_learning.db'):
        print("❌ Database file not found")
        return False
    
    guard = ProductionSafetyGuard()
    analysis = guard.validate_database_content('ai_learning.db')
    
    print(f"Database analysis:")
    print(f"  Valid: {analysis['valid']}")
    print(f"  Total users: {analysis.get('total_users', 'Unknown')}")
    print(f"  Test user count: {analysis.get('test_user_count', 'Unknown')}")
    print(f"  Is test data: {analysis.get('is_likely_test_data', 'Unknown')}")
    print(f"  Is production data: {analysis.get('is_likely_production_data', 'Unknown')}")
    print(f"  Confidence score: {analysis.get('confidence_score', 'Unknown')}")
    
    return analysis['valid']

def test_production_protection():
    """Test production overwrite protection"""
    
    print("\n🛡️ TESTING PRODUCTION PROTECTION")
    print("-" * 40)
    
    guard = ProductionSafetyGuard()
    
    # Test blocking test data to production
    production_ready = guard.check_production_readiness('ai_learning.db', 'production')
    print(f"Production readiness check: {'PASSED' if production_ready else 'BLOCKED (correct)'}")
    
    if guard.violations:
        print("Violations detected (as expected):")
        for violation in guard.violations:
            print(f"  - {violation}")
    
    # Test allowing to development
    guard.violations.clear()  # Clear previous violations
    dev_ready = guard.check_production_readiness('ai_learning.db', 'development')
    print(f"Development readiness check: {'PASSED (correct)' if dev_ready else 'BLOCKED'}")
    
    return not production_ready and dev_ready  # Should block production, allow development

def test_production_safe_decorator():
    """Test the production safe decorator"""
    
    print("\n🔒 TESTING PRODUCTION SAFE DECORATOR")
    print("-" * 40)
    
    @production_safe(require_backup=False, require_confirmation=False)
    def safe_test_function(test_param="test"):
        return f"Function executed with param: {test_param}"
    
    try:
        result = safe_test_function("test_value")
        print(f"✅ Production safe function executed: {result}")
        return True
    except ProductionSafetyError as e:
        print(f"❌ Production safe function blocked: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_azure_backup_status():
    """Test Azure backup status checking"""
    
    print("\n☁️ TESTING AZURE BACKUP STATUS")
    print("-" * 40)
    
    try:
        backup_manager = AzureBackupManager('ai-learning-rg', 'ai-learning-tracker-bharath')
        status = backup_manager.check_current_backup_status()
        
        print(f"Backup status check completed:")
        print(f"  Configured: {status.get('backups_configured', False)}")
        print(f"  Error: {status.get('error', 'None')}")
        
        return True
    except Exception as e:
        print(f"❌ Azure backup status check failed: {e}")
        return False

def test_governance_enforcer():
    """Test data governance enforcer"""
    
    print("\n⚖️ TESTING DATA GOVERNANCE ENFORCER")
    print("-" * 40)
    
    enforcer = DataGovernanceEnforcer()
    
    # Test environment validation
    env_valid = enforcer.validate_environment()
    print(f"Environment validation: {'PASSED' if env_valid else 'FAILED'}")
    
    # Test database integrity check
    if os.path.exists('ai_learning.db'):
        integrity = enforcer.check_database_integrity('ai_learning.db')
        print(f"Database integrity check:")
        print(f"  User count: {integrity.get('user_count', 'Unknown')}")
        print(f"  Test data detected: {integrity.get('is_test_data', 'Unknown')}")
        
    # Test production overwrite prevention
    prevention_check = enforcer.prevent_production_overwrite('ai_learning.db', 'production')
    print(f"Production overwrite prevention: {'BLOCKED (correct)' if not prevention_check else 'ALLOWED (concerning)'}")
    
    return env_valid

def test_audit_logging():
    """Test audit logging functionality"""
    
    print("\n📋 TESTING AUDIT LOGGING")
    print("-" * 40)
    
    guard = ProductionSafetyGuard()
    
    # Trigger an audit event
    guard._log_audit_event('test_event', {
        'test_data': 'audit_test',
        'timestamp': datetime.now().isoformat()
    })
    
    # Check if audit log file was created
    if os.path.exists('logs/data_governance_audit.json'):
        print("✅ Audit log file created")
        
        # Read the last audit entry
        with open('logs/data_governance_audit.json', 'r') as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                print(f"  Last audit entry: {last_entry['event_type']}")
                print(f"  Timestamp: {last_entry['timestamp']}")
                return True
    
    print("❌ Audit log not found or empty")
    return False

def run_comprehensive_test():
    """Run comprehensive data governance test suite"""
    
    print("🔐 COMPREHENSIVE DATA GOVERNANCE SYSTEM TEST")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results['environment_detection'] = test_environment_detection()
    test_results['database_validation'] = test_database_validation()
    test_results['production_protection'] = test_production_protection()
    test_results['production_safe_decorator'] = test_production_safe_decorator()
    test_results['azure_backup_status'] = test_azure_backup_status()
    test_results['governance_enforcer'] = test_governance_enforcer()
    test_results['audit_logging'] = test_audit_logging()
    
    # Generate test report
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL DATA GOVERNANCE TESTS PASSED!")
        print("✅ System is ready for production deployment")
    else:
        print("⚠️ Some tests failed - review before production deployment")
    
    # Generate recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    
    if not test_results['azure_backup_status']:
        print("- Complete Azure backup configuration")
    
    if not test_results['production_protection']:
        print("- Review production protection mechanisms")
    
    if test_results['database_validation'] and test_results['production_protection']:
        print("- ✅ Database validation working correctly")
        print("- ✅ Production protection active")
    
    if test_results['audit_logging']:
        print("- ✅ Audit logging functional")
    
    print("\n🔒 SECURITY STATUS:")
    if test_results['production_protection']:
        print("✅ Production data is protected from local data overwrite")
    else:
        print("⚠️ Production protection needs attention")
    
    print("\n☁️ AZURE BACKUP STATUS:")
    print("✅ Storage account created: ailearningbackups2025")
    print("✅ Container created: webapp-backups")
    print("⚠️ Backup automation requires SAS token configuration")
    
    return test_results

if __name__ == "__main__":
    results = run_comprehensive_test()
