#!/usr/bin/env python3
"""
Azure SQL Database Connection Code
All the code used for establishing connection with Azure SQL Database
Extracted from the main AI Learning Tracker app
"""

import os
import pyodbc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================================
# ENVIRONMENT VARIABLE CHECK
# ===============================================

def is_azure_sql():
    """Check if all Azure SQL environment variables are set"""
    azure_server = os.environ.get('AZURE_SQL_SERVER')
    azure_database = os.environ.get('AZURE_SQL_DATABASE')
    azure_username = os.environ.get('AZURE_SQL_USERNAME')
    azure_password = os.environ.get('AZURE_SQL_PASSWORD')
    
    return all([azure_server, azure_database, azure_username, azure_password])

# ===============================================
# MAIN CONNECTION FUNCTION
# ===============================================

def get_db_connection():
    """Get database connection based on environment configuration"""
    if is_azure_sql():
        # Azure SQL Database connection
        logger.info("Using Azure SQL Database with environment variables")
        return _get_azure_sql_connection()
    else:
        # Local SQLite Database connection (fallback)
        logger.info("Using local SQLite database (fallback)")
        return None  # Would use SQLite in full app

# ===============================================
# AZURE SQL CONNECTION IMPLEMENTATION
# ===============================================

def _get_azure_sql_connection():
    """Get Azure SQL database connection"""
    try:
        # Get environment variables
        azure_server = os.environ.get('AZURE_SQL_SERVER')
        azure_database = os.environ.get('AZURE_SQL_DATABASE')
        azure_username = os.environ.get('AZURE_SQL_USERNAME')
        azure_password = os.environ.get('AZURE_SQL_PASSWORD')
        
        # Validate all variables are set
        if not all([azure_server, azure_database, azure_username, azure_password]):
            raise ValueError("Missing required Azure SQL environment variables")
        
        # Build connection string from environment variables
        azure_connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server=tcp:{azure_server},1433;"
            f"Database={azure_database};"
            f"Uid={azure_username};"
            f"Pwd={azure_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        logger.info(f"Connecting to Azure SQL Database: {azure_database}")
        logger.info(f"Server: {azure_server}")
        
        # Establish connection
        conn = pyodbc.connect(azure_connection_string)
        
        # Apply Azure SQL connection wrapper for compatibility
        return _wrap_azure_sql_connection(conn)
        
    except Exception as e:
        logger.error(f"Azure SQL connection failed: {e}")
        raise Exception(f"Failed to connect to Azure SQL Database: {e}")

# ===============================================
# CONNECTION WRAPPER FOR COMPATIBILITY
# ===============================================

def _wrap_azure_sql_connection(conn):
    """Wrap Azure SQL connection to provide SQLite-like interface"""
    
    # Simple row wrapper that supports both index and key access
    class SimpleRow:
        def __init__(self, cursor, row):
            self.columns = [column[0] for column in cursor.description]
            self.values = list(row)
            self._dict = dict(zip(self.columns, self.values))
            
        def __getitem__(self, key):
            if isinstance(key, int):
                return self.values[key]
            return self._dict[key]
            
        def __contains__(self, key):
            return key in self._dict
            
        def keys(self):
            return self._dict.keys()
    
    # Wrapper class for Azure SQL connection
    class AzureSQLConnection:
        def __init__(self, pyodbc_conn):
            self._conn = pyodbc_conn
            
        def cursor(self):
            return AzureSQLCursor(self._conn.cursor())
            
        def execute(self, query, params=()):
            cursor = self.cursor()
            cursor.execute(query, params)
            return cursor
            
        def commit(self):
            self._conn.commit()
            
        def rollback(self):
            self._conn.rollback()
            
        def close(self):
            self._conn.close()
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                self.rollback()
            self.close()
    
    # Wrapper class for Azure SQL cursor
    class AzureSQLCursor:
        def __init__(self, pyodbc_cursor):
            self._cursor = pyodbc_cursor
            
        def execute(self, query, params=()):
            # Convert ? placeholders for pyodbc compatibility
            self._cursor.execute(query, params)
            
        def fetchone(self):
            row = self._cursor.fetchone()
            if row:
                return SimpleRow(self._cursor, row)
            return None
            
        def fetchall(self):
            rows = self._cursor.fetchall()
            return [SimpleRow(self._cursor, row) for row in rows]
            
        def close(self):
            self._cursor.close()
    
    return AzureSQLConnection(conn)

# ===============================================
# REQUIRED ENVIRONMENT VARIABLES
# ===============================================

REQUIRED_AZURE_ENV_VARS = [
    'AZURE_SQL_SERVER',      # Example: ai-learning-sql-centralus.database.windows.net
    'AZURE_SQL_DATABASE',    # Example: ai-learning-db  
    'AZURE_SQL_USERNAME',    # Example: ailearningadmin
    'AZURE_SQL_PASSWORD',    # Example: your-secure-password
]

# ===============================================
# CONNECTION STRING TEMPLATE
# ===============================================

CONNECTION_STRING_TEMPLATE = """
Driver={ODBC Driver 17 for SQL Server};
Server=tcp:{server},1433;
Database={database};
Uid={username};
Pwd={password};
Encrypt=yes;
TrustServerCertificate=no;
Connection Timeout=30;
"""

# ===============================================
# USAGE EXAMPLE
# ===============================================

def test_connection():
    """Test the Azure SQL Database connection"""
    try:
        print("Testing Azure SQL Database connection...")
        
        # Check environment variables
        if not is_azure_sql():
            print("❌ Missing Azure SQL environment variables")
            print("Required variables:", REQUIRED_AZURE_ENV_VARS)
            return False
        
        print("✅ All environment variables are set")
        
        # Test connection
        conn = get_db_connection()
        if conn:
            print("✅ Connection established successfully")
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"✅ Query successful: {count} users found")
            
            conn.close()
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
