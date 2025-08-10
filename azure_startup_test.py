#!/usr/bin/env python3
"""
Minimal test to identify Azure startup issues
"""
try:
    print("🔍 Testing Azure app startup...")
    
    # Test basic imports
    print("✅ Testing imports...")
    import os
    import sys
    import logging
    from flask import Flask
    print("✅ Basic imports successful")
    
    # Test Flask app creation
    print("✅ Testing Flask app creation...")
    app = Flask(__name__)
    print("✅ Flask app created successfully")
    
    # Test environment variables
    print("✅ Testing environment variables...")
    required_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
    else:
        print("✅ All Azure environment variables present")
    
    # Test database connection
    print("✅ Testing database connection...")
    try:
        import pyodbc
        print("✅ pyodbc import successful")
        
        # Try basic connection test
        server = os.environ.get('AZURE_SQL_SERVER')
        database = os.environ.get('AZURE_SQL_DATABASE') 
        username = os.environ.get('AZURE_SQL_USERNAME')
        password = os.environ.get('AZURE_SQL_PASSWORD')
        
        if all([server, database, username, password]):
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            
            try:
                conn = pyodbc.connect(connection_string)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()
                print("✅ Database connection successful")
            except Exception as db_e:
                print(f"❌ Database connection failed: {db_e}")
        else:
            print("⚠️  Database credentials not available for testing")
            
    except ImportError as e:
        print(f"❌ pyodbc import failed: {e}")
    
    print("🎉 Basic tests completed successfully!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
