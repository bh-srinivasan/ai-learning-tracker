#!/usr/bin/env python3
"""
Azure Database Table Creation Script
Ensures all required tables exist in Azure SQL database
"""

import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_azure_connection():
    """Get Azure SQL database connection"""
    try:
        connection_string = os.getenv('AZURE_DATABASE_CONNECTION_STRING')
        if not connection_string:
            print("❌ AZURE_DATABASE_CONNECTION_STRING environment variable not found")
            return None
        
        conn = pyodbc.connect(connection_string)
        print("✅ Connected to Azure SQL database")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to Azure SQL database: {e}")
        return None

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ?
        """, table_name)
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"❌ Error checking table {table_name}: {e}")
        return False

def create_user_sessions_table(conn):
    """Create user_sessions table"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE user_sessions (
                id NVARCHAR(255) PRIMARY KEY,
                user_id INT NOT NULL,
                session_token NVARCHAR(255) NOT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                expires_at DATETIME2 NOT NULL,
                is_active BIT DEFAULT 1,
                last_activity DATETIME2 DEFAULT GETDATE(),
                ip_address NVARCHAR(45),
                user_agent NVARCHAR(MAX),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("✅ Created user_sessions table")
        return True
    except Exception as e:
        print(f"❌ Error creating user_sessions table: {e}")
        return False

def create_courses_table(conn):
    """Create courses table"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE courses (
                id INT IDENTITY(1,1) PRIMARY KEY,
                title NVARCHAR(500) NOT NULL,
                description NVARCHAR(MAX),
                url NVARCHAR(1000),
                level NVARCHAR(50),
                points NVARCHAR(50),
                duration NVARCHAR(100),
                source NVARCHAR(100) DEFAULT 'Manual',
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                url_status NVARCHAR(50) DEFAULT 'Unknown',
                url_checked_at DATETIME2,
                difficulty NVARCHAR(50),
                prerequisites NVARCHAR(MAX),
                learning_objectives NVARCHAR(MAX),
                modules NVARCHAR(MAX),
                certification NVARCHAR(100),
                instructor NVARCHAR(200),
                rating DECIMAL(3,2),
                enrollment_count INT,
                last_updated DATETIME2,
                language NVARCHAR(50) DEFAULT 'English',
                price NVARCHAR(50) DEFAULT 'Free',
                category NVARCHAR(100),
                tags NVARCHAR(500),
                thumbnail_url NVARCHAR(1000)
            )
        """)
        conn.commit()
        print("✅ Created courses table")
        return True
    except Exception as e:
        print(f"❌ Error creating courses table: {e}")
        return False

def create_user_courses_table(conn):
    """Create user_courses table for tracking course progress"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE user_courses (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                course_id INT NOT NULL,
                status NVARCHAR(50) DEFAULT 'Not Started',
                progress_percentage INT DEFAULT 0,
                started_at DATETIME2,
                completed_at DATETIME2,
                last_accessed DATETIME2,
                notes NVARCHAR(MAX),
                rating INT,
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (course_id) REFERENCES courses(id),
                UNIQUE(user_id, course_id)
            )
        """)
        conn.commit()
        print("✅ Created user_courses table")
        return True
    except Exception as e:
        print(f"❌ Error creating user_courses table: {e}")
        return False

def main():
    """Main function to check and create required tables"""
    print("🔧 Azure Database Table Creation Script")
    print("="*50)
    
    # Connect to Azure database
    conn = get_azure_connection()
    if not conn:
        return
    
    try:
        # List of required tables and their creation functions
        tables_to_check = [
            ('user_sessions', create_user_sessions_table),
            ('courses', create_courses_table),
            ('user_courses', create_user_courses_table)
        ]
        
        for table_name, create_function in tables_to_check:
            print(f"\n📋 Checking table: {table_name}")
            
            if check_table_exists(conn, table_name):
                print(f"✅ Table {table_name} already exists")
            else:
                print(f"❌ Table {table_name} missing - creating...")
                if create_function(conn):
                    print(f"✅ Successfully created {table_name}")
                else:
                    print(f"❌ Failed to create {table_name}")
        
        print("\n" + "="*50)
        print("🎉 Azure database table creation completed!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()
