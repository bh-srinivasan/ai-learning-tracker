#!/usr/bin/env python3
"""
Azure SQL Database Initialization Script
Fixes the Azure deployment database issues by using proper SQL Server syntax
"""

import os
import logging
from database_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_azure_database():
    """Initialize Azure SQL database with proper schema and admin user"""
    try:
        logger.info("🔄 Starting Azure SQL database initialization...")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("❌ Database connection failed")
            return False
        
        logger.info(f"✅ Connected to {'Azure SQL' if db_manager.is_azure_sql else 'SQLite'}")
        
        # Create tables
        logger.info("🏗️ Creating database tables...")
        db_manager.create_tables()
        logger.info("✅ Database tables created successfully")
        
        # Create admin user if needed
        logger.info("👤 Checking admin user...")
        conn = db_manager.get_connection()
        
        try:
            if db_manager.is_azure_sql:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
                admin_count = cursor.fetchone()[0]
            else:
                admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0]
            
            if admin_count == 0:
                logger.info("🔐 Creating admin user...")
                from werkzeug.security import generate_password_hash
                admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
                password_hash = generate_password_hash(admin_password)
                
                if db_manager.is_azure_sql:
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, level, points, is_admin)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('admin', password_hash, 'Advanced', 100, 1))
                    conn.commit()
                else:
                    conn.execute("""
                        INSERT INTO users (username, password_hash, level, points, is_admin)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('admin', password_hash, 'Advanced', 100, 1))
                    conn.commit()
                
                logger.info("✅ Admin user created successfully")
            else:
                logger.info("✅ Admin user already exists")
                
        finally:
            conn.close()
        
        logger.info("🎉 Azure SQL database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = initialize_azure_database()
    exit(0 if success else 1)
