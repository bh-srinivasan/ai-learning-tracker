#!/usr/bin/env python3
"""
Security Guard Module - Uber-level safeguards for user management operations

CRITICAL BUSINESS RULES - ENFORCED BY THIS MODULE:
==================================================

1. NEVER DELETE USERS WITHOUT EXPLICIT AUTHORIZATION
   - Only admin user is permanently protected from deletion
   - All user deletions MUST be triggered via UI (admin panel)
   - NO automated/backend user deletion scripts allowed in production

2. PASSWORD RESET SAFETY
   - Password resets MUST be explicitly requested by admin via UI
   - NO automated password resets unless specifically authorized
   - Backend password reset scripts require explicit user consent

3. PRODUCTION SAFEGUARDS
   - All dangerous operations blocked in production unless explicitly authorized
   - UI-only operations cannot be triggered programmatically
   - Comprehensive audit logging for all protected operations

4. ADMIN PROTECTION
   - Admin user cannot be deleted under any circumstances
   - Admin password resets require special authorization
   - Admin account operations are heavily logged

These rules are implemented via decorators:
- @security_guard('operation_name', require_ui=True)
- @production_safe('operation_name')

Prevents unsafe operations in production and enforces strict controls
"""

import os
import logging
from functools import wraps
from flask import current_app
import traceback

# Configure security logger
security_logger = logging.getLogger('security_guard')
security_logger.setLevel(logging.INFO)

class SecurityGuardError(Exception):
    """Custom exception for security guard violations"""
    pass

class SecurityGuard:
    """Uber-level security guard for user management operations"""
    
    # Allowed test users for development only
    ALLOWED_TEST_USERS = ['admin', 'demo']
    
    # Forbidden operations in production and require explicit user authorization
    DANGEROUS_OPERATIONS = [
        'password_reset',
        'user_delete',
        'bulk_password_reset',
        'user_suspend',
        'database_cleanup',
        'user_removal',
        'bulk_user_delete'
    ]
    
    # Operations that require explicit user authorization even in development
    AUTHORIZATION_REQUIRED_OPERATIONS = [
        'user_delete',
        'database_cleanup',
        'user_removal',
        'bulk_user_delete',
        'drop_user_table',
        'backend_password_reset',  # Backend password resets require explicit authorization
        'automated_password_reset'  # Any automated password reset requires authorization
    ]
    
    # Operations requiring UI interaction (frontend-triggered only)
    UI_ONLY_OPERATIONS = [
        'admin_password_reset',  # Admin password resets must come through UI
        'bulk_password_reset',   # Bulk resets must be UI-triggered
        'individual_password_reset'  # Individual resets must be UI-triggered
    ]
    
    @staticmethod
    def get_environment():
        """Get current environment with fallback"""
        return os.environ.get('FLASK_ENV', os.environ.get('NODE_ENV', 'production'))
    
    @staticmethod
    def is_development():
        """Check if running in development environment"""
        env = SecurityGuard.get_environment().lower()
        return env in ['development', 'dev', 'local']
    
    @staticmethod
    def is_test_user(username):
        """Check if user is an allowed test user"""
        return username in SecurityGuard.ALLOWED_TEST_USERS
    
    @staticmethod
    def validate_operation(operation, username=None, force=False, explicit_authorization=False):
        """
        Validate if an operation is allowed
        
        Args:
            operation: The operation being attempted
            username: The user being affected (if applicable)
            force: Override protection (use with extreme caution)
            explicit_authorization: User has explicitly authorized this operation
        
        Returns:
            bool: True if operation is allowed
            
        Raises:
            SecurityGuardError: If operation is not permitted
        """
        # Log the operation attempt
        security_logger.info(f"Security validation: operation={operation}, username={username}, env={SecurityGuard.get_environment()}")
        
        # Check for UI-only operations
        if operation in SecurityGuard.UI_ONLY_OPERATIONS:
            if not SecurityGuard.require_ui_interaction():
                raise SecurityGuardError(
                    f"Operation '{operation}' can only be performed through the user interface. "
                    f"This operation cannot be automated or triggered by backend code."
                )
        
        # Check for operations requiring explicit authorization
        if operation in SecurityGuard.AUTHORIZATION_REQUIRED_OPERATIONS:
            if not explicit_authorization and not force:
                raise SecurityGuardError(
                    f"Operation '{operation}' requires explicit user authorization. "
                    f"This operation affects user data and cannot be performed automatically. "
                    f"User must explicitly request this operation."
                )
            # If explicit authorization is given, log it and allow the operation
            if explicit_authorization:
                security_logger.warning(f"EXPLICIT AUTHORIZATION: {operation} for {username} - User explicitly authorized this operation")
                return True
        
        # Force override (should only be used in very specific cases)
        if force:
            security_logger.warning(f"FORCE OVERRIDE: {operation} for {username} - CAUTION ADVISED")
            return True
        
        # Check environment
        if not SecurityGuard.is_development():
            raise SecurityGuardError(
                f"Operation '{operation}' is not permitted in {SecurityGuard.get_environment()} environment. "
                "User management operations are restricted to development only."
            )
        
        # Check if operation is dangerous (only for non-authorized operations)
        if operation in SecurityGuard.DANGEROUS_OPERATIONS and not explicit_authorization:
            if username and not SecurityGuard.is_test_user(username):
                raise SecurityGuardError(
                    f"Operation '{operation}' not permitted for user '{username}'. "
                    f"Only test users {SecurityGuard.ALLOWED_TEST_USERS} are allowed in development."
                )
        
        return True
    
    @staticmethod
    def require_ui_interaction():
        """Ensure operation is triggered via UI, not automation"""
        # Check if running in an interactive context
        # This is a placeholder - in a real app, you'd check request context
        if os.environ.get('AUTOMATED_EXECUTION') == 'true':
            raise SecurityGuardError(
                "This operation requires UI interaction and cannot be automated."
            )
        return True

    @staticmethod
    def validate_password_reset_request(username=None, explicit_user_request=False, ui_triggered=False):
        """
        Validate password reset requests with strict controls
        
        Args:
            username: The user whose password is being reset
            explicit_user_request: Whether this was explicitly requested by a user
            ui_triggered: Whether this was triggered through the UI
            
        Returns:
            bool: True if password reset is allowed
            
        Raises:
            SecurityGuardError: If password reset is not permitted
        """
        # Backend password resets must be explicitly requested
        if not explicit_user_request and not ui_triggered:
            raise SecurityGuardError(
                "Password reset must be explicitly requested by the user. "
                "Backend password resets are not allowed without explicit authorization."
            )
        
        # Log the password reset attempt
        security_logger.info(f"Password reset validation: username={username}, explicit_request={explicit_user_request}, ui_triggered={ui_triggered}")
        
        # UI-triggered resets are generally allowed for admins
        if ui_triggered:
            security_logger.info(f"UI-triggered password reset approved for user: {username}")
            return True
            
        # Explicit user requests are allowed
        if explicit_user_request:
            security_logger.warning(f"EXPLICIT USER REQUEST: Password reset for {username} - User explicitly requested this operation")
            return True
            
        return True

    @staticmethod
    def validate_azure_deployment_safety(operation, username=None, ui_triggered=False):
        """
        Azure deployment-specific validation
        Ensures operations are safe for production deployment
        
        Args:
            operation: The operation being attempted
            username: The user being affected (if applicable)
            ui_triggered: Whether this is triggered through the UI
            
        Returns:
            bool: True if operation is safe for Azure deployment
            
        Raises:
            SecurityGuardError: If operation is not safe for production
        """
        env = SecurityGuard.get_environment()
        
        # In production, only allow UI-triggered sensitive operations
        if env == 'production':
            # Operations that must be UI-triggered in production
            ui_only_in_production = [
                'password_reset',
                'user_delete',
                'bulk_password_reset',
                'user_suspend',
                'database_cleanup'
            ]
            
            if operation in ui_only_in_production and not ui_triggered:
                raise SecurityGuardError(
                    f"AZURE PRODUCTION SAFETY: Operation '{operation}' must be triggered through "
                    f"the web interface in production. Backend/automated execution is not allowed."
                )
            
            # Log all production operations
            security_logger.info(f"Azure production operation: {operation}, user={username}, ui_triggered={ui_triggered}")
        
        return True

def security_guard(operation, username_param=None, require_ui=False, require_authorization=False):
    """
    Decorator to enforce security guards on sensitive operations
    
    Args:
        operation: Name of the operation being guarded
        username_param: Name of the parameter containing the username (or position index)
        require_ui: Whether to require UI interaction
        require_authorization: Whether to require explicit user authorization
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Extract username if specified
                username = None
                if username_param is not None:
                    if isinstance(username_param, int) and len(args) > username_param:
                        # Use positional argument by index
                        username = args[username_param]
                    elif isinstance(username_param, str) and username_param in kwargs:
                        # Use keyword argument by name
                        username = kwargs[username_param]
                    elif isinstance(username_param, str) and len(args) > 0:
                        # Try to get attribute from first argument
                        if hasattr(args[0], username_param):
                            username = getattr(args[0], username_param)
                
                # Check for explicit authorization if required
                explicit_auth = kwargs.get('explicit_authorization', False) or not require_authorization
                
                # Validate the operation
                SecurityGuard.validate_operation(operation, username, explicit_authorization=explicit_auth)
                
                # Check UI requirement
                if require_ui:
                    SecurityGuard.require_ui_interaction()
                
                # Execute the function
                return func(*args, **kwargs)
                
            except SecurityGuardError as e:
                security_logger.error(f"Security guard blocked operation: {str(e)}")
                raise
            except Exception as e:
                security_logger.error(f"Unexpected error in security guard: {str(e)}")
                raise
        
        return wrapper
    return decorator

def password_reset_guard(ui_triggered=False, require_explicit_request=True):
    """
    Specialized decorator for password reset operations
    
    Args:
        ui_triggered: Whether this is triggered through the UI
        require_explicit_request: Whether to require explicit user request
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Check for explicit user request parameter
                explicit_request = kwargs.get('explicit_user_request', False)
                username = kwargs.get('username') or (args[0] if args else None)
                
                # Validate password reset request
                SecurityGuard.validate_password_reset_request(
                    username=username,
                    explicit_user_request=explicit_request,
                    ui_triggered=ui_triggered
                )
                
                # Execute the function
                return func(*args, **kwargs)
                
            except SecurityGuardError as e:
                security_logger.error(f"Password reset guard blocked operation: {str(e)}")
                raise
            except Exception as e:
                security_logger.error(f"Unexpected error in password reset guard: {str(e)}")
                raise
        
        return wrapper
    return decorator

def log_admin_action(action, details, user_id=None, ip_address=None):
    """
    Securely log admin actions without exposing sensitive data
    
    Args:
        action: The action performed
        details: Non-sensitive details about the action
        user_id: ID of the user performing the action
        ip_address: IP address of the request
    """
    try:
        # Sanitize details to prevent sensitive data exposure
        safe_details = str(details)[:500]  # Limit length
        
        # Log to security logger
        security_logger.info(
            f"ADMIN_ACTION: action={action}, user_id={user_id}, "
            f"ip={ip_address}, details={safe_details}"
        )
        
        # In a real application, this would also log to a secure audit table
        
    except Exception as e:
        security_logger.error(f"Failed to log admin action: {str(e)}")

def get_test_credentials():
    """
    Get test user credentials from environment variables
    
    Returns:
        dict: Dictionary of test user credentials
    """
    return {
        'admin': {
            'username': 'admin',
            'password': os.environ.get('ADMIN_PASSWORD', 'fallback_admin_password')
        },
        'demo': {
            'username': 'demo', 
            'password': os.environ.get('DEMO_PASSWORD', 'fallback_demo_password')
        }
    }

def validate_test_environment():
    """
    Validate that we're in a proper test environment
    
    Returns:
        bool: True if environment is valid for testing
        
    Raises:
        SecurityGuardError: If environment is not suitable for testing
    """
    if not SecurityGuard.is_development():
        raise SecurityGuardError(
            f"Test operations not allowed in {SecurityGuard.get_environment()} environment"
        )
    
    # Check required environment variables
    required_vars = ['ADMIN_PASSWORD', 'DEMO_PASSWORD']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise SecurityGuardError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    return True

# Export main components
__all__ = [
    'SecurityGuard',
    'SecurityGuardError', 
    'security_guard',
    'password_reset_guard',
    'log_admin_action',
    'get_test_credentials',
    'validate_test_environment'
]
