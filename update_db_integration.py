"""
Database Integration Script
This script updates the app.py to use the new database manager
"""

import re
import sys

def update_app_py():
    """Update app.py to integrate with database_manager"""
    
    # Read the current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import at the top (after existing imports)
    import_pattern = r'(from urllib\.parse import urlparse\n)'
    import_replacement = r'\1try:\n    from database_manager import get_db_connection as db_get_connection, init_database as db_init, db_manager\nexcept ImportError:\n    db_get_connection = None\n    db_init = None\n    db_manager = None\n'
    
    if 'from database_manager import' not in content:
        content = re.sub(import_pattern, import_replacement, content)
        print("✅ Added database_manager import")
    
    # Replace the get_db_connection function
    old_function = r'def get_db_connection\(\):\s*"""Get database connection with environment-aware logging"""\s*database_path = get_database_path\(\).*?return conn'
    
    new_function = '''def get_db_connection():
    """Get database connection with environment-aware support for Azure SQL"""
    try:
        # Check if we should use Azure SQL
        database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
        
        if (database_url == 'azure_sql' or production_safety.environment == 'production') and db_get_connection:
            logger.info(f"🌍 Environment: {production_safety.environment}")
            
            if db_manager and db_manager.is_azure_sql:
                logger.info("📂 Connecting to Azure SQL Database")
            else:
                logger.info("📂 Using SQLite via database manager")
            
            return db_get_connection()
        else:
            # Use traditional SQLite connection
            database_path = get_database_path()
            
            # Log database connection details for debugging
            logger.info(f"📂 Connecting to database: {os.path.abspath(database_path)}")
            logger.info(f"🌍 Environment: {production_safety.environment}")
            logger.info(f"💾 Database exists: {os.path.exists(database_path)}")
            
            if os.path.exists(database_path):
                logger.info(f"📊 Database size: {os.path.getsize(database_path)} bytes")
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row
            return conn
            
    except Exception as e:
        # Fallback to old method if there are any issues
        logger.warning(f"Database manager error ({e}), using fallback SQLite connection")
        database_path = get_database_path()
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return conn'''
    
    # Replace the function (use DOTALL flag to match across lines)
    content = re.sub(old_function, new_function, content, flags=re.DOTALL)
    print("✅ Updated get_db_connection function")
    
    # Add database initialization call in the main section
    main_pattern = r'(if __name__ == \'__main__\':)'
    main_replacement = r'# Initialize database on startup\ntry:\n    if db_init:\n        logger.info("🔄 Initializing database with Azure SQL support...")\n        db_init()\n        logger.info("✅ Database initialization completed")\nexcept Exception as e:\n    logger.error(f"❌ Database initialization failed: {e}")\n\n\1'
    
    if 'db_init()' not in content:
        content = re.sub(main_pattern, main_replacement, content)
        print("✅ Added database initialization")
    
    # Write the updated content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ App.py updated successfully!")

if __name__ == '__main__':
    update_app_py()
