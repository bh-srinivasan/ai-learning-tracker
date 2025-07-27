#!/usr/bin/env python3
"""
Database Environment Manager
Automatically handles database connection and schema creation for both local and production environments.
"""

import os
import sys
import logging
import sqlite3
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSchemaManager:
    """Manages database schema definition and creation for both SQLite and Azure SQL"""
    
    # Shared schema definition - single source of truth
    SCHEMA_DEFINITION = {
        'users': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'username VARCHAR(50) UNIQUE NOT NULL',
                'password_hash VARCHAR(255) NOT NULL',
                'level VARCHAR(20) DEFAULT "Beginner"',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'points INTEGER DEFAULT 0',
                'status VARCHAR(20) DEFAULT "active"',
                'user_selected_level VARCHAR(20)',
                'session_token VARCHAR(255)',
                'last_login TIMESTAMP',
                'last_activity TIMESTAMP',
                'login_count INTEGER DEFAULT 0',
                'password_reset_token VARCHAR(255)',
                'password_reset_expires TIMESTAMP',
                'level_points INTEGER DEFAULT 0',
                'level_updated_at TIMESTAMP'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
                'CREATE INDEX IF NOT EXISTS idx_users_level ON users(level)',
                'CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token)'
            ]
        },
        'learning_entries': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'user_id INTEGER NOT NULL',
                'title VARCHAR(200) NOT NULL',
                'description TEXT',
                'date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'tags TEXT',
                'custom_date DATE',
                'is_global BOOLEAN DEFAULT 0'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_learning_user_id ON learning_entries(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_learning_date_added ON learning_entries(date_added)',
                'CREATE INDEX IF NOT EXISTS idx_learning_is_global ON learning_entries(is_global)'
            ]
        },
        'courses': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'title VARCHAR(300) NOT NULL',
                'source VARCHAR(100)',
                'level VARCHAR(20)',
                'link VARCHAR(500)',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'points INTEGER DEFAULT 0',
                'description TEXT',
                'url VARCHAR(500)',
                'category VARCHAR(100)',
                'difficulty VARCHAR(20)',
                'url_status VARCHAR(50) DEFAULT "unknown"',
                'last_url_check TIMESTAMP'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_courses_source ON courses(source)',
                'CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level)',
                'CREATE INDEX IF NOT EXISTS idx_courses_category ON courses(category)',
                'CREATE INDEX IF NOT EXISTS idx_courses_url_status ON courses(url_status)'
            ]
        },
        'sessions': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'user_id INTEGER NOT NULL',
                'session_token VARCHAR(255) UNIQUE NOT NULL',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'expires_at TIMESTAMP NOT NULL',
                'ip_address VARCHAR(45)',
                'user_agent TEXT',
                'is_active BOOLEAN DEFAULT 1'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions(session_token)',
                'CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)'
            ]
        },
        'user_courses': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'user_id INTEGER NOT NULL',
                'course_id INTEGER NOT NULL',
                'completed BOOLEAN DEFAULT 0',
                'completion_date TIMESTAMP'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE',
                'FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_user_courses_user_id ON user_courses(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_user_courses_course_id ON user_courses(course_id)'
            ]
        },
        'level_settings': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'level_name VARCHAR(50) NOT NULL',
                'points_required INTEGER NOT NULL',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_level_settings_level_name ON level_settings(level_name)'
            ]
        },
        'course_search_configs': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'topic_name VARCHAR(100) NOT NULL',
                'search_keywords TEXT',
                'source VARCHAR(100)',
                'is_active BOOLEAN DEFAULT 1',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_course_search_topic ON course_search_configs(topic_name)',
                'CREATE INDEX IF NOT EXISTS idx_course_search_source ON course_search_configs(source)'
            ]
        },
        'user_personal_courses': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'user_id INTEGER NOT NULL',
                'title VARCHAR(300) NOT NULL',
                'source VARCHAR(100)',
                'course_url VARCHAR(500)',
                'description TEXT',
                'completion_date DATE',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_user_personal_courses_user_id ON user_personal_courses(user_id)'
            ]
        },
        'user_sessions': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'user_id INTEGER NOT NULL',
                'session_token VARCHAR(255) NOT NULL',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'expires_at TIMESTAMP NOT NULL',
                'ip_address VARCHAR(45)',
                'user_agent TEXT',
                'is_active BOOLEAN DEFAULT 1'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token)'
            ]
        },
        'session_activity': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'session_token VARCHAR(255) NOT NULL',
                'activity_type VARCHAR(100) NOT NULL',
                'activity_data TEXT',
                'timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'ip_address VARCHAR(45)'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_session_activity_token ON session_activity(session_token)',
                'CREATE INDEX IF NOT EXISTS idx_session_activity_type ON session_activity(activity_type)'
            ]
        },
        'security_events': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'event_type VARCHAR(100) NOT NULL',
                'details TEXT',
                'ip_address VARCHAR(45)',
                'user_id INTEGER',
                'timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)',
                'CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)'
            ]
        },
        'security_logs': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'event_type VARCHAR(100) NOT NULL',
                'description TEXT',
                'ip_address VARCHAR(45)',
                'user_id INTEGER',
                'timestamp DATETIME DEFAULT CURRENT_TIMESTAMP',
                'success BOOLEAN DEFAULT 1'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_security_logs_type ON security_logs(event_type)',
                'CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp)'
            ]
        },
        'points_log': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'user_id INTEGER NOT NULL',
                'course_id INTEGER',
                'action VARCHAR(100) NOT NULL',
                'points_change INTEGER NOT NULL',
                'points_before INTEGER',
                'points_after INTEGER',
                'reason TEXT',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            ],
            'foreign_keys': [
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE',
                'FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_points_log_user_id ON points_log(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_points_log_created_at ON points_log(created_at)'
            ]
        },
        'admin_actions': {
            'columns': [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'admin_user_id INTEGER NOT NULL',
                'action_type VARCHAR(100) NOT NULL',
                'target_type VARCHAR(100)',
                'target_id INTEGER',
                'description TEXT',
                'ip_address VARCHAR(45)',
                'user_agent TEXT',
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            ],
            'foreign_keys': [
                'FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE CASCADE'
            ],
            'indexes': [
                'CREATE INDEX IF NOT EXISTS idx_admin_actions_user ON admin_actions(admin_user_id)',
                'CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type)',
                'CREATE INDEX IF NOT EXISTS idx_admin_actions_created ON admin_actions(created_at)'
            ]
        }
    }

    @classmethod
    def get_sqlite_create_table_sql(cls, table_name: str) -> str:
        """Generate SQLite CREATE TABLE statement"""
        table_def = cls.SCHEMA_DEFINITION[table_name]
        columns = table_def['columns']
        foreign_keys = table_def.get('foreign_keys', [])
        
        all_constraints = columns + foreign_keys
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        sql += ",\n".join(f"    {constraint}" for constraint in all_constraints)
        sql += "\n)"
        
        return sql

    @classmethod
    def get_azure_sql_create_table_sql(cls, table_name: str) -> str:
        """Generate Azure SQL CREATE TABLE statement (converts SQLite syntax)"""
        table_def = cls.SCHEMA_DEFINITION[table_name]
        columns = table_def['columns']
        foreign_keys = table_def.get('foreign_keys', [])
        
        # Convert SQLite types to SQL Server types
        converted_columns = []
        for column in columns:
            # Replace SQLite-specific syntax with SQL Server equivalents
            azure_column = column.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'INT IDENTITY(1,1) PRIMARY KEY')
            azure_column = azure_column.replace('BOOLEAN', 'BIT')
            azure_column = azure_column.replace('TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'DATETIME2 DEFAULT GETDATE()')
            azure_column = azure_column.replace('DATETIME DEFAULT CURRENT_TIMESTAMP', 'DATETIME2 DEFAULT GETDATE()')
            azure_column = azure_column.replace('TIMESTAMP', 'DATETIME2')
            azure_column = azure_column.replace('TEXT', 'NVARCHAR(MAX)')
            
            # Fix quoted defaults for SQL Server
            azure_column = azure_column.replace('DEFAULT "Beginner"', "DEFAULT 'Beginner'")
            azure_column = azure_column.replace('DEFAULT "active"', "DEFAULT 'active'")
            azure_column = azure_column.replace('DEFAULT "unknown"', "DEFAULT 'unknown'")
            
            converted_columns.append(azure_column)
        
        all_constraints = converted_columns + foreign_keys
        sql = f"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')\n"
        sql += f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(f"    {constraint}" for constraint in all_constraints)
        sql += "\n)"
        
        return sql

    @classmethod
    def get_table_indexes(cls, table_name: str) -> List[str]:
        """Get index creation statements for a table"""
        return cls.SCHEMA_DEFINITION[table_name].get('indexes', [])


class DatabaseEnvironmentManager:
    """Manages database connections and schema creation based on environment"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.connection = None
        self.schema_manager = DatabaseSchemaManager()
        
        logger.info(f"🌍 Environment detected: {self.environment}")

    def _detect_environment(self) -> str:
        """Detect current environment from environment variables"""
        env = os.getenv('ENV', os.getenv('ENVIRONMENT', 'local')).lower()
        
        # Azure production indicators
        if any([
            env == 'production',
            env == 'prod',
            os.getenv('AZURE_WEBAPP_NAME'),
            os.getenv('WEBSITE_SITE_NAME'),
        ]):
            return 'production'
        
        return 'local'

    def _get_azure_sql_connection_string(self) -> str:
        """Build Azure SQL connection string from environment variables"""
        server = os.getenv('AZURE_SQL_SERVER')
        database = os.getenv('AZURE_SQL_DATABASE', 'ai_learning_db')
        username = os.getenv('AZURE_SQL_USERNAME')
        password = os.getenv('AZURE_SQL_PASSWORD')
        
        if not all([server, username, password]):
            missing = [var for var, val in [
                ('AZURE_SQL_SERVER', server),
                ('AZURE_SQL_USERNAME', username), 
                ('AZURE_SQL_PASSWORD', password)
            ] if not val]
            raise ValueError(f"Missing Azure SQL environment variables: {', '.join(missing)}")
        
        # Build connection string for pyodbc
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        return conn_str

    def _get_sqlite_connection_string(self) -> str:
        """Get SQLite database path"""
        db_path = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
        
        if db_path.startswith('sqlite:///'):
            return db_path.replace('sqlite:///', '')
        elif db_path.startswith('sqlite://'):
            return db_path.replace('sqlite://', '')
        
        return db_path

    def connect_to_database(self):
        """Connect to appropriate database based on environment"""
        if self.environment == 'production':
            self._connect_to_azure_sql()
        else:
            self._connect_to_sqlite()

    def _connect_to_sqlite(self):
        """Connect to local SQLite database"""
        try:
            db_path = self._get_sqlite_connection_string()
            logger.info(f"📂 Connecting to SQLite: {os.path.abspath(db_path)}")
            
            self.connection = sqlite3.connect(db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            
            logger.info("✅ SQLite connection established")
            
        except Exception as e:
            logger.error(f"❌ SQLite connection failed: {e}")
            raise

    def _connect_to_azure_sql(self):
        """Connect to Azure SQL Database"""
        try:
            import pyodbc
        except ImportError:
            logger.error("❌ pyodbc not installed. Install with: pip install pyodbc")
            raise ImportError("pyodbc is required for Azure SQL connections")

        try:
            conn_str = self._get_azure_sql_connection_string()
            logger.info("🔗 Connecting to Azure SQL Database...")
            
            # First, try to connect to the specific database
            try:
                self.connection = pyodbc.connect(conn_str)
                logger.info("✅ Azure SQL Database connection established")
                
            except pyodbc.Error as e:
                if "Cannot open database" in str(e):
                    logger.warning("📝 Database doesn't exist, creating it...")
                    self._create_azure_database()
                    self.connection = pyodbc.connect(conn_str)
                    logger.info("✅ Azure SQL Database connection established")
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Azure SQL connection failed: {e}")
            raise

    def _create_azure_database(self):
        """Create Azure SQL Database if it doesn't exist"""
        try:
            import pyodbc
            
            # Connect to master database to create new database
            server = os.getenv('AZURE_SQL_SERVER')
            username = os.getenv('AZURE_SQL_USERNAME')
            password = os.getenv('AZURE_SQL_PASSWORD')
            database_name = os.getenv('AZURE_SQL_DATABASE', 'ai_learning_db')
            
            master_conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE=master;"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
            
            logger.info(f"🏗️ Creating database: {database_name}")
            
            with pyodbc.connect(master_conn_str) as conn:
                conn.autocommit = True
                cursor = conn.cursor()
                
                # Check if database exists
                cursor.execute("""
                    SELECT database_id FROM sys.databases WHERE name = ?
                """, database_name)
                
                if not cursor.fetchone():
                    cursor.execute(f"CREATE DATABASE [{database_name}]")
                    logger.info(f"✅ Database '{database_name}' created successfully")
                else:
                    logger.info(f"ℹ️ Database '{database_name}' already exists")
                    
        except Exception as e:
            logger.error(f"❌ Failed to create Azure database: {e}")
            raise

    def create_schema(self):
        """Create all required tables and indexes"""
        if not self.connection:
            raise RuntimeError("No database connection established")

        logger.info("🏗️ Creating database schema...")
        
        try:
            if self.environment == 'production':
                self._create_azure_sql_schema()
            else:
                self._create_sqlite_schema()
                
            logger.info("✅ Schema creation completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            # For SQLite, check if it's a column issue and suggest migration
            if "no such column" in str(e) and self.environment == 'local':
                logger.warning("⚠️ Existing database schema differs from expected schema")
                logger.warning("⚠️ Consider backing up your data and running schema migration")
            raise

    def _create_sqlite_schema(self):
        """Create schema for SQLite database"""
        cursor = self.connection.cursor()
        
        # Create tables in dependency order
        table_order = [
            'users', 
            'learning_entries', 
            'courses', 
            'user_courses',
            'level_settings',
            'course_search_configs',
            'user_personal_courses',
            'sessions',
            'user_sessions', 
            'session_activity',
            'security_events',
            'security_logs',
            'points_log',
            'admin_actions'
        ]
        
        for table_name in table_order:
            logger.info(f"📋 Creating table: {table_name}")
            
            # Create table
            create_sql = self.schema_manager.get_sqlite_create_table_sql(table_name)
            cursor.execute(create_sql)
            
            # Create indexes
            for index_sql in self.schema_manager.get_table_indexes(table_name):
                cursor.execute(index_sql)
            
            logger.info(f"✅ Table '{table_name}' created with indexes")
        
        self.connection.commit()

    def _create_azure_sql_schema(self):
        """Create schema for Azure SQL Database"""
        cursor = self.connection.cursor()
        
        # Create tables in dependency order
        table_order = [
            'users', 
            'learning_entries', 
            'courses', 
            'user_courses',
            'level_settings',
            'course_search_configs',
            'user_personal_courses',
            'sessions',
            'user_sessions', 
            'session_activity',
            'security_events',
            'security_logs',
            'points_log',
            'admin_actions'
        ]
        
        for table_name in table_order:
            logger.info(f"📋 Creating table: {table_name}")
            
            # Create table
            create_sql = self.schema_manager.get_azure_sql_create_table_sql(table_name)
            cursor.execute(create_sql)
            
            # Create indexes (convert SQLite index syntax to SQL Server)
            for index_sql in self.schema_manager.get_table_indexes(table_name):
                # Convert SQLite index syntax to SQL Server
                azure_index_sql = index_sql.replace('IF NOT EXISTS', '')
                # Add existence check for SQL Server
                index_name = azure_index_sql.split(' ON ')[0].split()[-1]
                table_name_from_index = azure_index_sql.split(' ON ')[1].split('(')[0]
                
                check_sql = f"""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = '{index_name}' AND object_id = OBJECT_ID('{table_name_from_index}'))
                {azure_index_sql}
                """
                cursor.execute(check_sql)
            
            logger.info(f"✅ Table '{table_name}' created with indexes")
        
        self.connection.commit()

    def create_initial_data(self):
        """Create initial admin user and sample data"""
        if not self.connection:
            raise RuntimeError("No database connection established")

        logger.info("👤 Creating initial admin user...")
        
        try:
            cursor = self.connection.cursor()
            
            # Check if admin user exists
            if self.environment == 'production':
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
            else:
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
            
            if cursor.fetchone()[0] == 0:
                # Create admin user
                admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash(admin_password)
                
                if self.environment == 'production':
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, level, points, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('admin', password_hash, 'Advanced', 1000, 'active'))
                else:
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, level, points, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('admin', password_hash, 'Advanced', 1000, 'active'))
                
                self.connection.commit()
                logger.info("✅ Admin user created")
            else:
                logger.info("ℹ️ Admin user already exists")
                
        except Exception as e:
            logger.error(f"❌ Failed to create initial data: {e}")
            raise

    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")

    def test_connection(self):
        """Test database connection and basic operations"""
        if not self.connection:
            raise RuntimeError("No database connection established")

        try:
            cursor = self.connection.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM courses")
            course_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Database test successful:")
            logger.info(f"   Users: {user_count}")
            logger.info(f"   Courses: {course_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            return False


def main():
    """Main execution function"""
    logger.info("🚀 Starting Database Environment Manager")
    
    # Log environment variables (without sensitive data)
    env_vars = {
        'ENV': os.getenv('ENV', 'not set'),
        'ENVIRONMENT': os.getenv('ENVIRONMENT', 'not set'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'not set'),
        'AZURE_SQL_SERVER': os.getenv('AZURE_SQL_SERVER', 'not set'),
        'AZURE_SQL_DATABASE': os.getenv('AZURE_SQL_DATABASE', 'not set'),
        'AZURE_WEBAPP_NAME': os.getenv('AZURE_WEBAPP_NAME', 'not set'),
    }
    
    logger.info("🔧 Environment Configuration:")
    for key, value in env_vars.items():
        if 'PASSWORD' not in key and 'SECRET' not in key:
            logger.info(f"   {key}: {value}")

    db_manager = None
    
    try:
        # Initialize database manager
        db_manager = DatabaseEnvironmentManager()
        
        # Connect to database
        db_manager.connect_to_database()
        
        # Create schema
        db_manager.create_schema()
        
        # Create initial data
        try:
            db_manager.create_initial_data()
        except ImportError:
            logger.warning("⚠️ werkzeug not available, skipping admin user creation")
        
        # Test connection
        if db_manager.test_connection():
            logger.info("✅ Database setup completed successfully!")
        else:
            logger.error("❌ Database test failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return 1
        
    finally:
        if db_manager:
            db_manager.close_connection()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
