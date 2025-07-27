"""
Database initialization integration for Flask app
Add this to your main app.py file for automatic database setup
"""

import os
import logging
from database_environment_manager import DatabaseEnvironmentManager

logger = logging.getLogger(__name__)

def initialize_database_for_app():
    """
    Initialize database based on environment
    Call this in your Flask app initialization, before any database operations
    """
    logger.info("🔧 Initializing database for Flask app...")
    
    try:
        # Create database manager
        db_manager = DatabaseEnvironmentManager()
        
        # Connect and setup schema
        db_manager.connect_to_database()
        db_manager.create_schema()
        
        # Create initial data if needed
        try:
            db_manager.create_initial_data()
        except ImportError:
            logger.warning("⚠️ werkzeug not available for password hashing")
        except Exception as e:
            logger.warning(f"⚠️ Could not create initial data: {e}")
        
        # Test the connection
        if db_manager.test_connection():
            logger.info("✅ Database initialized successfully")
        else:
            logger.error("❌ Database test failed")
            
        # Close the setup connection (app will create its own connections)
        db_manager.close_connection()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def get_database_connection_config():
    """
    Get database connection configuration for the Flask app
    Returns the appropriate connection details based on environment
    """
    environment = os.getenv('ENV', os.getenv('ENVIRONMENT', 'local')).lower()
    
    if environment in ['production', 'prod'] or any([
        os.getenv('AZURE_WEBAPP_NAME'),
        os.getenv('WEBSITE_SITE_NAME'),
    ]):
        # Azure SQL Database configuration
        server = os.getenv('AZURE_SQL_SERVER')
        database = os.getenv('AZURE_SQL_DATABASE', 'ai_learning_db')
        username = os.getenv('AZURE_SQL_USERNAME')
        password = os.getenv('AZURE_SQL_PASSWORD')
        
        if all([server, username, password]):
            return {
                'type': 'azure_sql',
                'connection_string': (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={server};"
                    f"DATABASE={database};"
                    f"UID={username};"
                    f"PWD={password};"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=no;"
                    f"Connection Timeout=30;"
                ),
                'environment': 'production'
            }
        else:
            logger.warning("⚠️ Azure SQL credentials incomplete, falling back to SQLite")
    
    # SQLite configuration (local/fallback)
    db_path = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path.replace('sqlite:///', '')
    elif db_path.startswith('sqlite://'):
        db_path = db_path.replace('sqlite://', '')
    
    return {
        'type': 'sqlite',
        'path': db_path,
        'environment': 'local'
    }

# Example integration for your app.py:
"""
# Add this near the top of your app.py file, after Flask app creation:

from database_integration import initialize_database_for_app, get_database_connection_config

# Initialize database on app startup
if not initialize_database_for_app():
    logger.error("Failed to initialize database")
    # Handle error as appropriate for your app

# Get connection config for your existing database functions
db_config = get_database_connection_config()
logger.info(f"Using {db_config['type']} database in {db_config['environment']} environment")

# Update your get_db_connection() function to use the config:
def get_db_connection():
    db_config = get_database_connection_config()
    
    if db_config['type'] == 'azure_sql':
        import pyodbc
        return pyodbc.connect(db_config['connection_string'])
    else:
        import sqlite3
        conn = sqlite3.connect(db_config['path'])
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
"""
