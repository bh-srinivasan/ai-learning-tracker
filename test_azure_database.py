#!/usr/bin/env python3
"""
Test Azure SQL Database Connection and Setup Schema
"""

import os
import sys
from dotenv import load_dotenv

# Load Azure SQL environment variables
load_dotenv('.env.database.azure')

# Set environment variables
os.environ['ENV'] = 'production'
os.environ['AZURE_SQL_SERVER'] = 'ai-learning-sql-centralus.database.windows.net'
os.environ['AZURE_SQL_DATABASE'] = 'ai-learning-db'
os.environ['AZURE_SQL_USERNAME'] = 'ailearningadmin'
azure_sql_password = os.environ.get('AZURE_SQL_PASSWORD')
if not azure_sql_password:
    raise ValueError("AZURE_SQL_PASSWORD environment variable not set")
os.environ['AZURE_SQL_PASSWORD'] = azure_sql_password

print("🧪 Testing Azure SQL Database Connection and Schema Creation")
print("=" * 60)

try:
    from database_environment_manager import DatabaseEnvironmentManager
    
    # Initialize database manager
    print("🔧 Initializing database manager...")
    db_manager = DatabaseEnvironmentManager()
    
    print(f"🌍 Environment detected: {db_manager.environment}")
    
    # Connect to Azure SQL
    print("🔗 Connecting to Azure SQL Database...")
    db_manager.connect_to_database()
    print("✅ Connected successfully!")
    
    # Create schema
    print("🏗️ Creating database schema...")
    db_manager.create_schema()
    print("✅ Schema created successfully!")
    
    # Create initial data
    print("👤 Creating initial admin user...")
    try:
        db_manager.create_initial_data()
        print("✅ Initial data created successfully!")
    except Exception as e:
        print(f"⚠️ Initial data creation: {e}")
    
    # Test connection
    print("🧪 Testing database operations...")
    if db_manager.test_connection():
        print("✅ Database test passed!")
    else:
        print("❌ Database test failed!")
    
    # Close connection
    db_manager.close_connection()
    print("🔌 Connection closed")
    
    print("\n🎉 Azure SQL Database setup completed successfully!")
    print("\n📋 Database Details:")
    print(f"   Server: {os.environ['AZURE_SQL_SERVER']}")
    print(f"   Database: {os.environ['AZURE_SQL_DATABASE']}")
    print(f"   Username: {os.environ['AZURE_SQL_USERNAME']}")
    print("   Password: [CONFIGURED]")
    
    print("\n📝 Next Steps:")
    print("   1. Copy .env.database.azure to .env.database")
    print("   2. Update your Azure App Service environment variables")
    print("   3. Deploy your application to use Azure SQL Database")
    
except Exception as e:
    print(f"❌ Azure SQL Database test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
