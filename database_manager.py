"""
Azure SQL Database Connection Module

This module handles the connection to Azure SQL Database and provides
proper database initialization and migration from SQLite if needed.
"""

import os
import sqlite3
import pyodbc
import logging
from typing import Optional, Any, Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections for both SQLite (local) and Azure SQL (production)"""
    
    def __init__(self):
        self.connection_string = None
        self.is_azure_sql = False
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup database connection based on environment"""
        env = os.environ.get('ENV', 'development').lower()
        
        if env == 'production' and self._has_azure_sql_config():
            # Use Azure SQL in production
            self.connection_string = self._build_azure_sql_connection_string()
            self.is_azure_sql = True
            logger.info("✅ Using Azure SQL Database")
        else:
            # Use SQLite for development
            self.connection_string = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
            self.is_azure_sql = False
            logger.info("✅ Using SQLite Database")
    
    def _has_azure_sql_config(self) -> bool:
        """Check if Azure SQL configuration is available"""
        required_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
        return all(os.environ.get(var) for var in required_vars)
    
    def _build_azure_sql_connection_string(self) -> str:
        """Build Azure SQL connection string"""
        server = os.environ.get('AZURE_SQL_SERVER')
        database = os.environ.get('AZURE_SQL_DATABASE')
        username = os.environ.get('AZURE_SQL_USERNAME')
        password = os.environ.get('AZURE_SQL_PASSWORD')
        
        # Use ODBC Driver 18 for SQL Server (available in Azure)
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
    
    def get_connection(self):
        """Get database connection"""
        if self.is_azure_sql:
            return pyodbc.connect(self.connection_string)
        else:
            conn = sqlite3.connect(self.connection_string)
            conn.row_factory = sqlite3.Row
            return conn
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            if self.is_azure_sql:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            else:
                conn.execute("SELECT 1")
            conn.close()
            logger.info(f"✅ Database connection test successful ({'Azure SQL' if self.is_azure_sql else 'SQLite'})")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def create_tables(self):
        """Create database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.is_azure_sql:
                # Azure SQL table creation
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                    CREATE TABLE users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username NVARCHAR(80) UNIQUE NOT NULL,
                        password_hash NVARCHAR(255) NOT NULL,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        level NVARCHAR(20) DEFAULT 'Beginner',
                        points INT DEFAULT 0,
                        profile_picture NVARCHAR(255),
                        bio NTEXT,
                        is_admin BIT DEFAULT 0
                    )
                """)
                
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='learning_entries' AND xtype='U')
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
                """)
                
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='courses' AND xtype='U')
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
                """)
                
            else:
                # SQLite table creation
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level TEXT DEFAULT 'Beginner',
                        points INTEGER DEFAULT 0,
                        profile_picture TEXT,
                        bio TEXT,
                        is_admin INTEGER DEFAULT 0
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        topic TEXT NOT NULL,
                        description TEXT,
                        date_learned DATE NOT NULL,
                        time_spent INTEGER,
                        difficulty TEXT,
                        tags TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        level TEXT,
                        duration_hours INTEGER,
                        provider TEXT,
                        url TEXT,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active INTEGER DEFAULT 1
                    )
                ''')
            
            conn.commit()
            logger.info("✅ Database tables created/verified")
            
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def migrate_from_sqlite_if_needed(self, sqlite_path: str = None):
        """Migrate data from SQLite to Azure SQL if needed"""
        if not self.is_azure_sql:
            logger.info("Not using Azure SQL, skipping migration")
            return
        
        if not sqlite_path:
            sqlite_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
        
        if not os.path.exists(sqlite_path):
            logger.info("No SQLite database found for migration")
            return
        
        try:
            # Check if Azure SQL already has data
            azure_conn = self.get_connection()
            azure_cursor = azure_conn.cursor()
            azure_cursor.execute("SELECT COUNT(*) FROM users")
            user_count = azure_cursor.fetchone()[0]
            azure_conn.close()
            
            if user_count > 0:
                logger.info("Azure SQL already has data, skipping migration")
                return
            
            logger.info("Starting migration from SQLite to Azure SQL...")
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connect to Azure SQL
            azure_conn = self.get_connection()
            azure_cursor = azure_conn.cursor()
            
            # Migrate users
            sqlite_cursor.execute("SELECT * FROM users")
            users = sqlite_cursor.fetchall()
            
            for user in users:
                azure_cursor.execute("""
                    INSERT INTO users (username, password_hash, created_at, level, points, profile_picture, bio, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['username'], user['password_hash'], user['created_at'],
                    user['level'], user['points'], user.get('profile_picture'),
                    user.get('bio'), user.get('is_admin', 0)
                ))
            
            logger.info(f"Migrated {len(users)} users")
            
            # Migrate learning entries
            sqlite_cursor.execute("SELECT * FROM learning_entries")
            entries = sqlite_cursor.fetchall()
            
            for entry in entries:
                azure_cursor.execute("""
                    INSERT INTO learning_entries (user_id, topic, description, date_learned, time_spent, difficulty, tags, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry['user_id'], entry['topic'], entry['description'],
                    entry['date_learned'], entry['time_spent'], entry['difficulty'],
                    entry['tags'], entry['notes'], entry['created_at']
                ))
            
            logger.info(f"Migrated {len(entries)} learning entries")
            
            # Migrate courses if they exist
            try:
                sqlite_cursor.execute("SELECT * FROM courses")
                courses = sqlite_cursor.fetchall()
                
                for course in courses:
                    azure_cursor.execute("""
                        INSERT INTO courses (title, description, level, duration_hours, provider, url, tags, created_at, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        course['title'], course['description'], course['level'],
                        course['duration_hours'], course['provider'], course['url'],
                        course['tags'], course['created_at'], course.get('is_active', 1)
                    ))
                
                logger.info(f"Migrated {len(courses)} courses")
            except Exception as e:
                logger.warning(f"Could not migrate courses (table may not exist): {e}")
            
            azure_conn.commit()
            sqlite_conn.close()
            azure_conn.close()
            
            logger.info("✅ Migration completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

def get_db_connection():
    """Get database connection - compatible with existing code"""
    return db_manager.get_connection()

def init_database():
    """Initialize database - compatible with existing code"""
    try:
        # Test connection first
        if not db_manager.test_connection():
            raise Exception("Database connection test failed")
        
        # Create tables
        db_manager.create_tables()
        
        # Migrate from SQLite if using Azure SQL
        if db_manager.is_azure_sql:
            db_manager.migrate_from_sqlite_if_needed()
        
        logger.info("✅ Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
