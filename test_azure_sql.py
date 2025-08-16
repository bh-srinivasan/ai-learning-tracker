"""
Test Azure SQL Database Connection
"""
import os
import pyodbc

def test_azure_sql_connection():
    """Test Azure SQL Database connectivity"""
    try:
        server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
        database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
        username = os.environ.get('AZURE_SQL_USERNAME', 'ailearningadmin')
        password = os.environ.get('AZURE_SQL_PASSWORD')
        if not password:
            raise ValueError("AZURE_SQL_PASSWORD environment variable not set")
        
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        print(f"Testing connection to {server}/{database}...")
        
        # Test connection
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test_value")
        result = cursor.fetchone()
        print(f"✅ Connection successful! Test query result: {result[0]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        tables = cursor.fetchall()
        print(f"📊 Existing tables: {[table[0] for table in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == '__main__':
    test_azure_sql_connection()
