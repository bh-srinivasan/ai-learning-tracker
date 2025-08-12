import pyodbc
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Check Azure SQL table schema
server = os.environ.get('AZURE_SQL_SERVER', 'ai-learning-sql-centralus.database.windows.net')
database = os.environ.get('AZURE_SQL_DATABASE', 'ai-learning-db')
username = os.environ.get('AZURE_SQL_USERNAME', 'ailearningadmin')
password = os.environ.get('AZURE_SQL_PASSWORD')

# Validate required environment variables
if not password:
    print("❌ ERROR: AZURE_SQL_PASSWORD environment variable is required!")
    print("Please set it in your .env file or environment variables.")
    sys.exit(1)

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("=================================")
print("Azure SQL Schema Analysis")
print("=================================")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Get user_sessions table schema
    print("📋 user_sessions table columns:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'user_sessions'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col[0]} ({col[1]}) - Nullable: {col[2]}, Default: {col[3]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
