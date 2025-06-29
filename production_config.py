
# Production Configuration for Azure
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Database configuration for Azure
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
    
    # User credentials
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    DEMO_USERNAME = os.environ.get('DEMO_USERNAME', 'demo')
    DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD')
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    
    # Protected users
    PROTECTED_USERS = ['bharath']
