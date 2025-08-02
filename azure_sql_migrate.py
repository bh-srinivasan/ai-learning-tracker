#!/usr/bin/env python3
"""
Azure SQL Database Schema Migration Script
Ensures the database schema is properly created with SQL Server syntax
"""

import os
import pyodbc
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_azure_sql_connection():
    """Get Azure SQL connection using environment variables"""
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USERNAME')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    if not all([server, database, username, password]):
        logger.error("❌ Missing Azure SQL environment variables")
        return None
    
    # Build connection string
    conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    
    try:
        conn = pyodbc.connect(conn_str)
        logger.info("✅ Connected to Azure SQL Database")
        return conn
    except Exception as e:
        logger.error(f"❌ Azure SQL connection failed: {e}")
        return None

def create_azure_sql_schema():
    """Create database schema using proper SQL Server syntax"""
    conn = get_azure_sql_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Create users table
        logger.info("🏗️ Creating users table...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users')
            BEGIN
                CREATE TABLE users (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(80) UNIQUE NOT NULL,
                    password_hash NVARCHAR(255) NOT NULL,
                    level NVARCHAR(20) DEFAULT 'Beginner',
                    points INT DEFAULT 0,
                    status NVARCHAR(20) DEFAULT 'active',
                    user_selected_level NVARCHAR(20) DEFAULT 'Beginner',
                    created_at DATETIME2 DEFAULT GETDATE(),
                    last_login DATETIME2,
                    last_activity DATETIME2,
                    login_count INT DEFAULT 0,
                    session_token NVARCHAR(255),
                    password_reset_token NVARCHAR(255),
                    password_reset_expires DATETIME2,
                    is_admin BIT DEFAULT 0
                )
            END
        """)
        
        # Create learning_entries table
        logger.info("🏗️ Creating learning_entries table...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'learning_entries')
            BEGIN
                CREATE TABLE learning_entries (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL,
                    topic NVARCHAR(200) NOT NULL,
                    description NTEXT,
                    date_learned DATE NOT NULL,
                    time_spent INT,
                    difficulty NVARCHAR(20),
                    tags NVARCHAR(500),
                    notes NTEXT,
                    created_at DATETIME2 DEFAULT GETDATE(),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            END
        """)
        
        # Create courses table
        logger.info("🏗️ Creating courses table...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'courses')
            BEGIN
                CREATE TABLE courses (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    title NVARCHAR(255) NOT NULL,
                    description NTEXT,
                    level NVARCHAR(50),
                    duration_hours INT,
                    provider NVARCHAR(100),
                    url NVARCHAR(500),
                    tags NVARCHAR(500),
                    created_at DATETIME2 DEFAULT GETDATE(),
                    is_active BIT DEFAULT 1
                )
            END
        """)
        
        # Create user_sessions table
        logger.info("🏗️ Creating user_sessions table...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'user_sessions')
            BEGIN
                CREATE TABLE user_sessions (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL,
                    session_token NVARCHAR(255) UNIQUE NOT NULL,
                    created_at DATETIME2 DEFAULT GETDATE(),
                    expires_at DATETIME2 NOT NULL,
                    ip_address NVARCHAR(45),
                    user_agent NVARCHAR(500),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            END
        """)
        
        conn.commit()
        logger.info("✅ Database schema created successfully")
        
        # Create admin user if it doesn't exist
        logger.info("👤 Checking admin user...")
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            from werkzeug.security import generate_password_hash
            admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
            password_hash = generate_password_hash(admin_password)
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, level, points, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, ('admin', password_hash, 'Advanced', 100, 1))
            conn.commit()
            logger.info("✅ Admin user created")
        else:
            logger.info("✅ Admin user already exists")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🔄 Starting Azure SQL schema migration...")
    success = create_azure_sql_schema()
    if success:
        logger.info("🎉 Schema migration completed successfully!")
        exit(0)
    else:
        logger.error("💥 Schema migration failed!")
        exit(1)
