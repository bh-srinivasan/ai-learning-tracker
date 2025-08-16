#!/usr/bin/env python3
"""
Test script to verify database integration with Flask app pattern
"""

import os
import sys
import logging
from database_integration import initialize_database_for_app, get_database_connection_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_flask_integration():
    """Test the Flask integration functions"""
    print("🧪 Testing Flask Database Integration")
    print("=" * 50)
    
    # Test 1: Initialize database
    print("\n1. Testing database initialization...")
    if initialize_database_for_app():
        print("✅ Database initialization successful")
    else:
        print("❌ Database initialization failed")
        return False
    
    # Test 2: Get connection config
    print("\n2. Testing connection configuration...")
    config = get_database_connection_config()
    print(f"📊 Database Type: {config['type']}")
    print(f"🌍 Environment: {config['environment']}")
    
    if config['type'] == 'sqlite':
        print(f"📁 Database Path: {config['path']}")
    elif config['type'] == 'azure_sql':
        print(f"🔗 Connection String: [MASKED]")
    
    # Test 3: Test actual connection using the pattern
    print("\n3. Testing connection using Flask pattern...")
    try:
        if config['type'] == 'azure_sql':
            import pyodbc
            conn = pyodbc.connect(config['connection_string'])
        else:
            import sqlite3
            conn = sqlite3.connect(config['path'])
            conn.execute("PRAGMA foreign_keys = ON")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0]
        
        print(f"✅ Connection test successful")
        print(f"👥 Users in database: {user_count}")
        print(f"📚 Courses in database: {course_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Flask integration is ready to use.")
    return True

if __name__ == "__main__":
    if test_flask_integration():
        print("\n✅ Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)
