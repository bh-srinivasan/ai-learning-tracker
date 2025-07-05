
#!/usr/bin/env python3
"""
Production Environment Configuration
Azure deployment configuration with comprehensive production safeguards
"""

import os
import logging
from functools import wraps
from typing import Dict, Any

class ProductionConfig:
    """Production environment configuration and safeguards"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Database configuration for Azure
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
    
    # User credentials (environment-based)
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    DEMO_USERNAME = os.environ.get('DEMO_USERNAME', 'demo')
    DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD')
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 12))  # Stronger in production
    
    # Production security restrictions
    ALLOW_BULK_OPERATIONS = False  # No bulk operations in production
    REQUIRE_UI_FOR_SENSITIVE_OPS = True  # All sensitive operations must be UI-triggered
    ENABLE_PASSWORD_RESET_API = False  # No API password resets in production
    ALLOW_USER_REGISTRATION = False  # Disable registration in production
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    
    # Audit and logging
    ENABLE_AUDIT_LOGGING = True
    REQUIRE_HTTPS = True
    SECURE_COOKIES = True
    ENFORCE_CSRF_PROTECTION = True
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment"""
        return os.environ.get('FLASK_ENV', os.environ.get('NODE_ENV', 'production')).lower()
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment"""
        env = ProductionConfig.get_environment()
        return env in ['production', 'prod']
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development environment"""
        env = ProductionConfig.get_environment()
        return env in ['development', 'dev', 'local']
    
    @staticmethod
    def validate_production_safety(operation: str, context: str = "") -> bool:
        """
        Validate that operation is safe for production deployment
        
        Args:
            operation: The operation being performed
            context: Additional context (ui_triggered, explicit_request, etc.)
            
        Returns:
            bool: True if operation is safe for production
            
        Raises:
            Exception: If operation is not safe for production
        """
        if not ProductionConfig.is_production():
            return True  # Allow all operations in non-production
        
        # Production-safe operations (always allowed)
        safe_operations = [
            'ui_triggered_password_reset',  # Admin UI operations
            'authenticated_user_action',    # User self-service
            'audit_logging',               # Security logging
            'read_operations',             # Data reading
            'session_management',          # User sessions
            'user_login',                  # Authentication
            'user_profile_update'          # Profile changes
        ]
        
        # Operations requiring UI authorization in production
        restricted_operations = [
            'backend_password_reset',      # Backend scripts
            'bulk_user_operations',        # Bulk operations
            'user_deletion',              # User removal
            'database_cleanup',           # Database maintenance
            'administrative_override'      # Admin overrides
        ]
        
        if operation in safe_operations:
            return True
        
        if operation in restricted_operations:
            if 'ui_triggered' in context and 'authenticated_admin' in context:
                logging.info(f"Production operation authorized: {operation} (UI-triggered admin action)")
                return True
            else:
                raise Exception(
                    f"PRODUCTION SAFETY: Operation '{operation}' requires UI authorization in production. "
                    f"Context: {context}. Use admin web interface for this operation."
                )
        
        # Default: allow but log warning
        logging.warning(f"Production warning: Unclassified operation '{operation}' with context '{context}'")
        return True
    
    @staticmethod
    def validate_environment_variables() -> Dict[str, str]:
        """Validate required environment variables for production"""
        required_vars = {
            'FLASK_SECRET_KEY': 'Flask application secret key',
            'ADMIN_PASSWORD': 'Admin user password',
            'DEMO_PASSWORD': 'Demo user password',
        }
        
        if ProductionConfig.is_production():
            required_vars.update({
                'DATABASE_URL': 'Production database URL (if not using SQLite)',
            })
        
        missing_vars = {}
        for var, description in required_vars.items():
            if not os.environ.get(var):
                missing_vars[var] = description
        
        return missing_vars
    
    @staticmethod
    def setup_production_logging():
        """Setup production-appropriate logging"""
        if ProductionConfig.is_production():
            # Production logging - structured, secure
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),  # Azure App Service will capture this
                ]
            )
            
            # Disable debug logging in production
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
            
            # Enable security audit logging
            security_logger = logging.getLogger('security_audit')
            security_logger.setLevel(logging.INFO)
            
        else:
            # Development logging - verbose
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )

def production_safe(operation_type: str):
    """
    Decorator to ensure operations are safe for production deployment
    
    Args:
        operation_type: Type of operation being performed
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine context
            context = []
            if hasattr(func, '__name__') and 'admin' in func.__name__:
                context.append('authenticated_admin')
            if kwargs.get('ui_triggered', False):
                context.append('ui_triggered')
            if kwargs.get('explicit_user_request', False):
                context.append('explicit_user_request')
            
            context_str = ','.join(context) if context else 'no_context'
            
            # Validate production safety
            ProductionConfig.validate_production_safety(operation_type, context_str)
            
            # Log operation in production
            if ProductionConfig.is_production():
                logger = logging.getLogger('security_audit')
                logger.info(f"Production operation: {operation_type} with context: {context_str}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Environment configuration classes
class DevelopmentConfig:
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 7200))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    
    # Relaxed restrictions for development
    ALLOW_BULK_OPERATIONS = True
    REQUIRE_UI_FOR_SENSITIVE_OPS = False
    ENABLE_PASSWORD_RESET_API = True
    ALLOW_USER_REGISTRATION = True
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 10))

def get_config() -> Dict[str, Any]:
    """Get environment-appropriate configuration"""
    if ProductionConfig.is_production():
        return ProductionConfig()
    else:
        return DevelopmentConfig()

# Export configuration
__all__ = [
    'ProductionConfig',
    'DevelopmentConfig',
    'production_safe',
    'get_config'
]
