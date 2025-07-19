#!/usr/bin/env python3
"""
Azure-Specific Database Investigation Script

This script automatically detects whether it's running locally or on Azure
and performs environment-specific deep analysis of database initialization issues.
"""
import sqlite3
import os
import sys
import platform
from datetime import datetime, timezone
import subprocess
import json

class EnvironmentDetector:
    """Detect if we're running locally or on Azure"""
    
    @staticmethod
    def is_azure():
        """Detect if running on Azure App Service"""
        azure_indicators = [
            'WEBSITE_SITE_NAME',           # Azure App Service
            'WEBSITE_RESOURCE_GROUP',      # Azure App Service
            'WEBSITE_INSTANCE_ID',         # Azure App Service
            'SCM_REPOSITORY_PATH',         # Azure deployment
            'AZURE_CLIENT_ID',             # Azure authentication
        ]
        
        for indicator in azure_indicators:
            if os.getenv(indicator):
                return True
        
        # Check for Azure-specific paths
        azure_paths = [
            '/home/site/wwwroot',           # Azure Linux App Service
            'D:\\home\\site\\wwwroot',      # Azure Windows App Service
        ]
        
        for path in azure_paths:
            if os.path.exists(path):
                return True
        
        return False
    
    @staticmethod
    def get_environment_info():
        """Get comprehensive environment information"""
        return {
            'platform': platform.platform(),
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'environment_variables': {k: v for k, v in os.environ.items() if 'AZURE' in k or 'WEBSITE' in k or 'SCM' in k},
            'is_azure': EnvironmentDetector.is_azure()
        }

class AzureDatabaseInvestigator:
    """Azure-specific database investigation"""
    
    def __init__(self):
        self.db_path = 'ai_learning.db'
        self.is_azure = EnvironmentDetector.is_azure()
        self.env_info = EnvironmentDetector.get_environment_info()
        
    def analyze_database_persistence(self):
        """Analyze database persistence on Azure"""
        print("\n🔍 AZURE DATABASE PERSISTENCE ANALYSIS")
        print("=" * 70)
        
        if not self.is_azure:
            print("❌ NOT RUNNING ON AZURE - Switching to local analysis")
            self.analyze_local_database()
            return
            
        print(f"✅ CONFIRMED: Running on Azure App Service")
        
        # Check Azure environment details
        print("\n📋 AZURE ENVIRONMENT DETAILS:")
        print("-" * 40)
        for key, value in self.env_info['environment_variables'].items():
            print(f"  {key}: {value}")
            
        # Analyze database location and persistence
        self.analyze_azure_database_location()
        self.analyze_azure_file_system()
        self.check_azure_database_recreation_pattern()
        
    def analyze_azure_database_location(self):
        """Analyze where the database is stored on Azure"""
        print(f"\n📁 AZURE DATABASE LOCATION ANALYSIS:")
        print("-" * 40)
        
        current_dir = os.getcwd()
        db_full_path = os.path.join(current_dir, self.db_path)
        
        print(f"Current Directory: {current_dir}")
        print(f"Database Path: {db_full_path}")
        
        # Check if database exists
        if os.path.exists(db_full_path):
            stat = os.stat(db_full_path)
            print(f"✅ Database exists: {db_full_path}")
            print(f"   Size: {stat.st_size} bytes")
            print(f"   Created: {datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)}")
            print(f"   Modified: {datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)}")
            
            # Check if in ephemeral storage
            if '/tmp' in db_full_path or '\\temp' in db_full_path.lower():
                print("🚨 CRITICAL: Database is in EPHEMERAL storage - will be lost on restart!")
            elif '/home/site/wwwroot' in db_full_path:
                print("⚠️  WARNING: Database is in application directory - may be overwritten on deployment")
            else:
                print(f"📍 Database location: {db_full_path}")
                
        else:
            print(f"❌ Database not found: {db_full_path}")
            
    def analyze_azure_file_system(self):
        """Analyze Azure file system and persistence"""
        print(f"\n💾 AZURE FILE SYSTEM ANALYSIS:")
        print("-" * 40)
        
        # Check Azure storage locations
        azure_locations = [
            '/home/site/wwwroot',           # App files (ephemeral)
            '/home',                        # Home directory
            '/tmp',                         # Temporary (ephemeral)
            '/home/site/repository',        # Git repository
            '/home/LogFiles',              # Log files (persistent)
        ]
        
        for location in azure_locations:
            if os.path.exists(location):
                print(f"📂 {location}: EXISTS")
                try:
                    # Check if writable
                    test_file = os.path.join(location, 'test_write_access.tmp')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    print(f"   ✅ Writable")
                except:
                    print(f"   ❌ Not writable")
            else:
                print(f"📂 {location}: NOT FOUND")
                
    def check_azure_database_recreation_pattern(self):
        """Check for Azure-specific database recreation patterns"""
        print(f"\n🔄 AZURE DATABASE RECREATION PATTERN ANALYSIS:")
        print("-" * 40)
        
        if not os.path.exists(self.db_path):
            print("❌ Database file not found - cannot analyze recreation pattern")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Check users and their creation times
            users = conn.execute("SELECT username, created_at FROM users ORDER BY created_at").fetchall()
            print(f"Total users: {len(users)}")
            
            if users:
                print("\n👥 USER CREATION TIMELINE:")
                for user in users:
                    print(f"   {user['username']}: {user['created_at']}")
                    
                # Check if all users were created recently (indicating recreation)
                newest_user = users[-1]['created_at']
                newest_time = datetime.fromisoformat(newest_user)
                time_since_newest = datetime.now() - newest_time
                
                if time_since_newest.total_seconds() < 3600:  # Less than 1 hour
                    print(f"🚨 CRITICAL: All users created within last hour!")
                    print(f"   Most recent user: {time_since_newest.total_seconds():.0f} seconds ago")
                    print(f"   This indicates database was recreated during deployment!")
                else:
                    print(f"✅ Users have older timestamps - database may be persisting")
                    
            else:
                print("❌ No users found - database may have been initialized but users not created")
                
            conn.close()
            
        except Exception as e:
            print(f"❌ Error analyzing database: {e}")
            
    def check_azure_deployment_triggers(self):
        """Check what triggers database recreation on Azure deployment"""
        print(f"\n🚀 AZURE DEPLOYMENT TRIGGER ANALYSIS:")
        print("-" * 40)
        
        # Check Azure deployment environment variables
        deployment_vars = {
            'SCM_COMMIT_ID': 'Git commit that triggered deployment',
            'SCM_REPOSITORY_PATH': 'Repository path',
            'WEBSITE_SCM_TYPE': 'Source control type',
            'SCM_BUILD_CONFIGURATION': 'Build configuration'
        }
        
        print("📋 Deployment Information:")
        for var, description in deployment_vars.items():
            value = os.getenv(var, 'Not set')
            print(f"   {var}: {value} ({description})")
            
        # Check if this is a fresh deployment
        commit_id = os.getenv('SCM_COMMIT_ID')
        if commit_id:
            print(f"\n📝 Current deployment commit: {commit_id}")
            
        # Look for deployment-specific files
        deployment_files = [
            'deployment.log',
            'oryx-build.log',
            '.azure',
            'requirements.txt',
            'runtime.txt'
        ]
        
        print(f"\n📁 Deployment Files:")
        for file in deployment_files:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file}")
                
    def analyze_safe_init_db_behavior(self):
        """Analyze safe_init_db behavior in Azure environment"""
        print(f"\n🛡️ SAFE_INIT_DB BEHAVIOR ANALYSIS:")
        print("-" * 40)
        
        try:
            # Import the function
            sys.path.insert(0, '.')
            from app import safe_init_db, DATABASE
            import inspect
            
            print(f"Database path configured as: {DATABASE}")
            
            # Get source code
            source = inspect.getsource(safe_init_db)
            
            # Check for Azure-specific issues
            if 'os.path.exists' in source:
                print("✅ Function checks file existence")
            else:
                print("❌ Function does NOT check file existence - DANGEROUS!")
                
            # Test the actual file existence check
            db_exists = os.path.exists(DATABASE)
            print(f"Current database exists: {db_exists}")
            
            if db_exists:
                print("✅ Database file exists - safe_init_db should preserve it")
            else:
                print("❌ Database file missing - safe_init_db will create new one")
                
        except Exception as e:
            print(f"❌ Error analyzing safe_init_db: {e}")
            
    def analyze_local_database(self):
        """Analyze local database (fallback when not on Azure)"""
        print("\n🖥️  LOCAL DATABASE ANALYSIS:")
        print("-" * 40)
        
        print(f"Working Directory: {os.getcwd()}")
        print(f"Database Path: {self.db_path}")
        
        if os.path.exists(self.db_path):
            stat = os.stat(self.db_path)
            print(f"✅ Local database exists")
            print(f"   Size: {stat.st_size} bytes")
            print(f"   Modified: {datetime.fromtimestamp(stat.st_mtime)}")
            
            # Check local users
            try:
                conn = sqlite3.connect(self.db_path)
                users = conn.execute("SELECT username, created_at FROM users").fetchall()
                print(f"   Users: {len(users)}")
                for username, created_at in users:
                    print(f"     - {username}: {created_at}")
                conn.close()
                
            except Exception as e:
                print(f"   Error reading users: {e}")
        else:
            print("❌ Local database not found")
            
    def run_comprehensive_analysis(self):
        """Run complete environment-aware investigation"""
        print("🚀 AZURE/LOCAL DATABASE INVESTIGATION")
        print("=" * 80)
        print(f"Environment: {'AZURE' if self.is_azure else 'LOCAL'}")
        print(f"Platform: {self.env_info['platform']}")
        print(f"Working Directory: {self.env_info['working_directory']}")
        print("=" * 80)
        
        # Core analysis
        self.analyze_database_persistence()
        
        if self.is_azure:
            self.check_azure_deployment_triggers()
            
        self.analyze_safe_init_db_behavior()
        
        # Final recommendations
        self.provide_recommendations()
        
    def provide_recommendations(self):
        """Provide environment-specific recommendations"""
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        
        if self.is_azure:
            print("🔥 AZURE-SPECIFIC ISSUES IDENTIFIED:")
            print("   1. Azure App Service file system is EPHEMERAL")
            print("   2. Database file gets wiped on every deployment/restart")
            print("   3. safe_init_db() creates new database because file doesn't exist")
            print("\n🛠️  AZURE SOLUTIONS:")
            print("   1. Use Azure SQL Database (recommended)")
            print("   2. Use Azure Storage Account for SQLite file")
            print("   3. Use persistent volume mounting")
            print("   4. Implement database backup/restore on deployment")
        else:
            print("🖥️  LOCAL ENVIRONMENT:")
            print("   - Database should persist between restarts")
            print("   - Check for local issues with safe_init_db logic")

if __name__ == "__main__":
    investigator = AzureDatabaseInvestigator()
    investigator.run_comprehensive_analysis()
