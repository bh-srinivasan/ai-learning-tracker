"""
Configuration management for AI Learning Tracker
Loads environment variables and provides default values
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration from environment variables"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'change-this-in-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
    
    # User credentials (for demo/testing purposes)
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
    DEMO_USERNAME = os.environ.get('DEMO_USERNAME', 'demo')
    DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD', 'demo')
    
    # Protected admin users (should not be modified in testing)
    PROTECTED_USERS = ['bharath']  # These users should not be modified during testing
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour default
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    
    @staticmethod
    def get_admin_password():
        """Get admin password from environment"""
        return Config.ADMIN_PASSWORD
    
    @staticmethod
    def get_demo_username():
        """Get demo username from environment"""
        return Config.DEMO_USERNAME
    
    @staticmethod
    def get_demo_password():
        """Get demo user password from environment"""
        return Config.DEMO_PASSWORD
    
    @staticmethod
    def is_protected_user(username):
        """Check if user should be protected from testing modifications"""
        return username in Config.PROTECTED_USERS
    
    @staticmethod
    def is_production():
        """Check if running in production environment"""
        return Config.FLASK_ENV == 'production'
    
    @staticmethod
    def validate_config():
        """Validate critical configuration values"""
        warnings = []
        
        if Config.SECRET_KEY == 'change-this-in-production':
            warnings.append("WARNING: Using default SECRET_KEY - change this in production!")
            
        if Config.ADMIN_PASSWORD == 'admin':
            warnings.append("WARNING: Using default admin password - change this in production!")
            
        if Config.DEMO_PASSWORD == 'demo':
            warnings.append("WARNING: Using default demo password - change this in production!")
            
        if Config.DEMO_USERNAME == 'demo':
            warnings.append("INFO: Using 'demo' as demo username for testing")
            
        return warnings

# Development configuration
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    TESTING = False

# Production configuration
class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    TESTING = False

# Testing configuration
class TestingConfig(Config):
    """Testing-specific configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///test_ai_learning.db'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on FLASK_ENV"""
    return config.get(os.environ.get('FLASK_ENV', 'development'), DevelopmentConfig)
