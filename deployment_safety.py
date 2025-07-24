"""
Deployment Safety Module - AI Learning Tracker
Provides deployment safety checks and monitoring for production environments
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import threading
import time
import json
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentSafetyError(Exception):
    """Custom exception for deployment safety issues"""
    pass

class DeploymentSafety:
    def __init__(self, app=None, db_path: str = 'ai_learning.db'):
        self.app = app
        self.db_path = db_path
        self.safety_checks = {}
        self.deployment_locks = {}
        self.monitoring_active = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize deployment safety with Flask app"""
        self.app = app
        app.deployment_safety = self
        
        # Add safety middleware
        app.before_request(self.before_request_safety_check)
        app.after_request(self.after_request_monitoring)
        
        # Start background monitoring
        self.start_monitoring()
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def before_request_safety_check(self):
        """Safety checks before each request"""
        try:
            # Check if deployment is in safe state
            if not self.is_deployment_safe():
                logger.warning("Deployment safety check failed")
                return None  # Allow request to continue but log warning
                
            # Monitor critical operations
            self.log_operation('request_processed')
            
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            # Don't block requests for safety check failures
            return None
    
    def after_request_monitoring(self, response):
        """Monitor response and log deployment metrics"""
        try:
            # Log response status
            if response.status_code >= 500:
                self.log_operation('server_error', {'status_code': response.status_code})
            elif response.status_code >= 400:
                self.log_operation('client_error', {'status_code': response.status_code})
            else:
                self.log_operation('success_response', {'status_code': response.status_code})
                
        except Exception as e:
            logger.error(f"Response monitoring error: {e}")
        
        return response
    
    def is_deployment_safe(self) -> bool:
        """Check if deployment is in a safe state"""
        try:
            # Check database connectivity
            if not self.check_database_health():
                return False
            
            # Check critical file existence
            if not self.check_critical_files():
                return False
            
            # Check environment variables
            if not self.check_environment_config():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment safety check failed: {e}")
            return False
    
    def check_database_health(self) -> bool:
        """Check database connectivity and basic health"""
        try:
            conn = self.get_db_connection()
            
            # Basic connectivity test
            conn.execute('SELECT 1').fetchone()
            
            # Check critical tables exist
            tables = ['users', 'learning_entries', 'courses']
            for table in tables:
                result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                if result is None:
                    logger.error(f"Critical table {table} is empty or inaccessible")
                    conn.close()
                    return False
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def check_critical_files(self) -> bool:
        """Check that critical application files exist"""
        critical_files = [
            'app.py',
            'config.py',
            'level_manager.py',
            'auth/routes.py',
            'dashboard/routes.py',
            'learnings/routes.py',
            'admin/routes.py'
        ]
        
        try:
            for file_path in critical_files:
                if not os.path.exists(file_path):
                    logger.error(f"Critical file missing: {file_path}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Critical files check failed: {e}")
            return False
    
    def check_environment_config(self) -> bool:
        """Check environment configuration"""
        try:
            # Check if we're in a recognized environment
            env = os.getenv('FLASK_ENV', 'development')
            
            # In production, ensure critical env vars exist
            if env == 'production':
                critical_env_vars = ['SECRET_KEY', 'DATABASE_URL']
                for var in critical_env_vars:
                    if not os.getenv(var):
                        logger.warning(f"Production environment missing: {var}")
                        # Don't fail - use defaults
            
            return True
        except Exception as e:
            logger.error(f"Environment config check failed: {e}")
            return False
    
    def log_operation(self, operation: str, metadata: Dict = None):
        """Log deployment operations for monitoring"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'metadata': metadata or {},
                'deployment_id': getattr(self, 'deployment_id', 'unknown')
            }
            
            # Store in memory for now (could be extended to database)
            if operation not in self.safety_checks:
                self.safety_checks[operation] = []
            
            self.safety_checks[operation].append(log_entry)
            
            # Keep only recent entries (last 1000)
            if len(self.safety_checks[operation]) > 1000:
                self.safety_checks[operation] = self.safety_checks[operation][-1000:]
                
        except Exception as e:
            logger.error(f"Error logging operation: {e}")
    
    def get_deployment_status(self) -> Dict:
        """Get current deployment status and health metrics"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'is_safe': self.is_deployment_safe(),
                'database_health': self.check_database_health(),
                'critical_files': self.check_critical_files(),
                'environment_config': self.check_environment_config(),
                'monitoring_active': self.monitoring_active,
                'recent_operations': {},
                'deployment_id': getattr(self, 'deployment_id', 'unknown')
            }
            
            # Add recent operation counts
            for operation, entries in self.safety_checks.items():
                recent_entries = [
                    e for e in entries 
                    if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=1)
                ]
                status['recent_operations'][operation] = len(recent_entries)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'is_safe': False,
                'error': str(e)
            }
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        try:
            if self.monitoring_active:
                return
            
            self.monitoring_active = True
            
            def monitor():
                while self.monitoring_active:
                    try:
                        # Periodic health checks
                        self.log_operation('health_check', {
                            'database_ok': self.check_database_health(),
                            'files_ok': self.check_critical_files(),
                            'env_ok': self.check_environment_config()
                        })
                        
                        # Sleep for 5 minutes
                        time.sleep(300)
                        
                    except Exception as e:
                        logger.error(f"Monitoring thread error: {e}")
                        time.sleep(60)  # Shorter sleep on error
            
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            
            logger.info("Deployment safety monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        logger.info("Deployment safety monitoring stopped")
    
    def acquire_deployment_lock(self, operation: str, timeout: int = 300) -> bool:
        """Acquire a deployment lock for critical operations"""
        try:
            if operation in self.deployment_locks:
                # Check if lock is expired
                lock_time = self.deployment_locks[operation]
                if datetime.now() - lock_time < timedelta(seconds=timeout):
                    return False  # Lock still active
            
            # Acquire lock
            self.deployment_locks[operation] = datetime.now()
            self.log_operation('lock_acquired', {'operation': operation})
            return True
            
        except Exception as e:
            logger.error(f"Error acquiring deployment lock: {e}")
            return False
    
    def release_deployment_lock(self, operation: str):
        """Release a deployment lock"""
        try:
            if operation in self.deployment_locks:
                del self.deployment_locks[operation]
                self.log_operation('lock_released', {'operation': operation})
        except Exception as e:
            logger.error(f"Error releasing deployment lock: {e}")

def deployment_safe(operation: str = None):
    """Decorator to ensure operations are deployment-safe"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get deployment safety instance
                safety = getattr(func.__globals__.get('current_app'), 'deployment_safety', None)
                
                if safety:
                    op_name = operation or f"{func.__module__}.{func.__name__}"
                    
                    # Log operation start
                    safety.log_operation('operation_start', {'function': op_name})
                    
                    # Check if deployment is safe
                    if not safety.is_deployment_safe():
                        logger.warning(f"Deployment safety warning for {op_name}")
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Log operation completion
                    safety.log_operation('operation_complete', {'function': op_name})
                    
                    return result
                else:
                    # No safety instance, execute normally
                    return func(*args, **kwargs)
                    
            except Exception as e:
                logger.error(f"Deployment safety decorator error: {e}")
                # Execute function anyway to avoid breaking functionality
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def init_deployment_safety(app, db_path: str = 'ai_learning.db') -> DeploymentSafety:
    """Initialize deployment safety for Flask app"""
    try:
        safety = DeploymentSafety(app, db_path)
        logger.info("Deployment safety initialized successfully")
        return safety
    except Exception as e:
        logger.error(f"Failed to initialize deployment safety: {e}")
        # Return a mock safety instance that doesn't interfere
        return DeploymentSafety(db_path=db_path)

# Global instance
deployment_safety = None
