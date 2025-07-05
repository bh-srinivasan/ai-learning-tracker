#!/usr/bin/env python3
"""
Production Safety Guard - Prevents data governance violations
Implements multi-layer protection against production data mishandling
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from functools import wraps

class ProductionSafetyError(Exception):
    """Raised when a production safety violation is detected"""
    pass

class ProductionSafetyGuard:
    """Multi-layer protection system for production data integrity"""
    
    def __init__(self):
        self.violations = []
        self.environment = self._detect_environment()
        self.audit_log = []
        
    def _detect_environment(self) -> str:
        """Detect current environment based on indicators"""
        
        # Azure production indicators
        if any([
            os.getenv('AZURE_WEBAPP_NAME'),
            os.getenv('WEBSITE_SITE_NAME'),
            os.getenv('WEBSITE_RESOURCE_GROUP')
        ]):
            return 'production'
        
        # Development indicators
        if any([
            os.getenv('FLASK_ENV') == 'development',
            os.getenv('ENVIRONMENT') == 'development',
            os.path.exists('.env.development')
        ]):
            return 'development'
        
        # Default to development for safety
        return 'development'
    
    def _log_audit_event(self, event_type: str, details: Dict):
        """Log audit event for compliance"""
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'environment': self.environment,
            'details': details,
            'user': os.getenv('USER', 'unknown'),
            'hostname': os.getenv('COMPUTERNAME', 'unknown')
        }
        
        self.audit_log.append(audit_entry)
        
        # Write to audit file
        os.makedirs('logs', exist_ok=True)
        with open('logs/data_governance_audit.json', 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
    
    def validate_database_content(self, db_path: str) -> Dict:
        """Validate database content to determine if it's production or test data"""
        
        if not os.path.exists(db_path):
            return {'valid': False, 'error': 'Database file not found'}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users table
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT username FROM users LIMIT 10")
            users = [row[0] for row in cursor.fetchall()]
            
            # Analyze user data patterns
            test_patterns = ['admin', 'demo', 'test', 'jane_doe', 'test_user', 'sample']
            
            test_users = sum(1 for username in users 
                           if any(pattern in username.lower() for pattern in test_patterns))
            
            analysis = {
                'valid': True,
                'total_users': user_count,
                'sample_users': users,
                'test_user_count': test_users,
                'is_likely_test_data': test_users > 0 and test_users / len(users) > 0.5 if users else True,
                'is_likely_production_data': user_count > 50 and test_users == 0,
                'confidence_score': self._calculate_confidence_score(users, user_count)
            }
            
            conn.close()
            return analysis
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _calculate_confidence_score(self, users: List[str], user_count: int) -> float:
        """Calculate confidence score for data type classification"""
        
        if not users:
            return 0.0
        
        # Factors that indicate test data
        test_score = 0.0
        
        # Check for test usernames
        test_patterns = ['admin', 'demo', 'test', 'jane', 'sample', 'user']
        for username in users:
            if any(pattern in username.lower() for pattern in test_patterns):
                test_score += 0.2
        
        # Small user count indicates test data
        if user_count < 10:
            test_score += 0.3
        elif user_count < 50:
            test_score += 0.1
        
        return min(test_score, 1.0)
    
    def check_production_readiness(self, data_source: str, target_env: str) -> bool:
        """Check if data is ready for production deployment"""
        
        self._log_audit_event('production_readiness_check', {
            'data_source': data_source,
            'target_environment': target_env
        })
        
        if target_env != 'production':
            return True
        
        # Validate data source
        if data_source.endswith('.db'):
            analysis = self.validate_database_content(data_source)
            
            if not analysis['valid']:
                violation = f"❌ Database validation failed: {analysis['error']}"
                self.violations.append(violation)
                return False
            
            if analysis['is_likely_test_data']:
                violation = f"❌ BLOCKED: Test data detected in source for production deployment"
                violation += f"\n   Test users: {analysis['test_user_count']}/{analysis['total_users']}"
                violation += f"\n   Confidence: {analysis['confidence_score']:.2f}"
                self.violations.append(violation)
                return False
        
        return True
    
    def require_explicit_confirmation(self, operation: str, risks: List[str]) -> bool:
        """Require explicit confirmation for dangerous operations"""
        
        print(f"\n🚨 DANGEROUS OPERATION DETECTED: {operation}")
        print("⚠️ RISKS:")
        for risk in risks:
            print(f"   - {risk}")
        
        print(f"\nEnvironment: {self.environment}")
        print("Type 'CONFIRM_DANGEROUS_OPERATION' to proceed:")
        
        confirmation = input().strip()
        confirmed = confirmation == 'CONFIRM_DANGEROUS_OPERATION'
        
        self._log_audit_event('explicit_confirmation', {
            'operation': operation,
            'risks': risks,
            'confirmed': confirmed,
            'confirmation_text': confirmation
        })
        
        return confirmed

def production_safe(require_backup=True, require_confirmation=True):
    """Decorator to make functions production-safe"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            guard = ProductionSafetyGuard()
            
            # Check environment
            if guard.environment == 'production':
                
                # Require backup verification
                if require_backup:
                    print("🔍 Checking backup status...")
                    # In real implementation, check Azure backup status
                    print("⚠️ Backup verification required but not implemented")
                
                # Require explicit confirmation
                if require_confirmation:
                    operation = f"{func.__name__}({args}, {kwargs})"
                    risks = [
                        "May modify production data",
                        "Could cause data loss",
                        "Affects real users",
                        "Irreversible changes possible"
                    ]
                    
                    if not guard.require_explicit_confirmation(operation, risks):
                        raise ProductionSafetyError("Operation cancelled by user")
            
            # Execute function
            try:
                result = func(*args, **kwargs)
                
                guard._log_audit_event('function_execution', {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs),
                    'success': True
                })
                
                return result
                
            except Exception as e:
                guard._log_audit_event('function_execution', {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs),
                    'success': False,
                    'error': str(e)
                })
                raise
        
        return wrapper
    return decorator

@production_safe(require_backup=True, require_confirmation=True)
def deploy_database_changes(source_db: str, target_env: str):
    """Deploy database changes with production safety"""
    
    guard = ProductionSafetyGuard()
    
    # Validate deployment
    if not guard.check_production_readiness(source_db, target_env):
        violations_text = '\n'.join(guard.violations)
        raise ProductionSafetyError(f"Production readiness check failed:\n{violations_text}")
    
    print(f"✅ Deploying database changes from {source_db} to {target_env}")
    
    # In real implementation, perform deployment
    return True

@production_safe(require_backup=True, require_confirmation=True) 
def reset_user_data(user_id: Optional[str] = None):
    """Reset user data with production safety"""
    
    print(f"🔄 Resetting user data for: {user_id or 'ALL USERS'}")
    
    # In real implementation, perform reset
    return True

def main():
    """Test the production safety system"""
    
    print("🛡️ PRODUCTION SAFETY GUARD SYSTEM")
    print("=" * 50)
    
    guard = ProductionSafetyGuard()
    print(f"Detected environment: {guard.environment}")
    
    # Test database validation
    if os.path.exists('ai_learning.db'):
        print("\n🔍 Testing database validation...")
        analysis = guard.validate_database_content('ai_learning.db')
        print(f"Database analysis: {json.dumps(analysis, indent=2)}")
        
        # Test production readiness check
        print("\n🔍 Testing production readiness...")
        ready = guard.check_production_readiness('ai_learning.db', 'production')
        print(f"Production ready: {ready}")
        
        if guard.violations:
            print("\n❌ Violations found:")
            for violation in guard.violations:
                print(f"   {violation}")
    
    # Test decorated functions (commented out to avoid actual execution)
    print("\n📋 Production-safe functions available:")
    print("   - deploy_database_changes()")
    print("   - reset_user_data()")
    print("   - [Add other functions as needed]")
    
    print("\n✅ Production safety system initialized")

if __name__ == "__main__":
    main()
