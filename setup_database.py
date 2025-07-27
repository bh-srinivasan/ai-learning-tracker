#!/usr/bin/env python3
"""
Quick setup script for AI Learning Tracker database
Automates the initial database setup process
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main setup process"""
    print("🚀 AI Learning Tracker Database Setup")
    print("=" * 50)
    
    # Check if .env.database exists
    env_file = Path('.env.database')
    if not env_file.exists():
        print("📋 Creating .env.database from template...")
        template_file = Path('.env.database.template')
        if template_file.exists():
            # Copy template to .env.database
            with open(template_file, 'r') as template:
                content = template.read()
            with open(env_file, 'w') as env:
                env.write(content)
            print("✅ Created .env.database file")
            print("⚠️  Please edit .env.database with your specific values")
        else:
            print("❌ .env.database.template not found")
            return False
    else:
        print("✅ .env.database already exists")
    
    # Load environment variables from .env.database
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.database')
        print("✅ Loaded environment variables from .env.database")
    except ImportError:
        print("⚠️  python-dotenv not installed, loading variables manually...")
        with open('.env.database', 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Import and run database setup
    try:
        from database_environment_manager import DatabaseEnvironmentManager
        
        print("\n🔧 Setting up database...")
        db_manager = DatabaseEnvironmentManager()
        
        # Connect and setup
        db_manager.connect_to_database()
        print("✅ Connected to database")
        
        db_manager.create_schema()
        print("✅ Database schema created")
        
        try:
            db_manager.create_initial_data()
            print("✅ Initial data created")
        except Exception as e:
            print(f"⚠️  Could not create initial data: {e}")
        
        if db_manager.test_connection():
            print("✅ Database test passed")
            print("\n🎉 Database setup completed successfully!")
            
            # Show connection info
            env = db_manager.environment
            db_type = "Azure SQL" if env == "production" else "SQLite"
            print(f"📊 Using {db_type} database in {env} environment")
            
            return True
        else:
            print("❌ Database test failed")
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        logger.exception("Setup error details:")
        return False
    
    finally:
        try:
            db_manager.close_connection()
        except:
            pass
    
    return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        print("You can now run your Flask app with: python app.py")
