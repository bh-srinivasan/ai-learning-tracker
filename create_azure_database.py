#!/usr/bin/env python3
"""
Azure SQL Database Setup Script
Creates Azure SQL Server and Database for AI Learning Tracker
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime

class AzureSQLSetup:
    def __init__(self):
        self.resource_group = "ai-learning-rg"
        self.location = "eastus"
        self.server_name = "ai-learning-sql-server"
        self.database_name = "ai-learning-db"
        self.admin_username = "ailearningadmin"
        self.admin_password = os.environ.get('ADMIN_PASSWORD')
        if not self.admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable not set")
        
    def run_az_command(self, command):
        """Run Azure CLI command and return result"""
        try:
            print(f"🔧 Running: {command}")
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {e}")
            print(f"Error output: {e.stderr}")
            return None

    def check_provider_registration(self):
        """Check if Microsoft.Sql provider is registered"""
        print("🔍 Checking Microsoft.Sql provider registration...")
        
        command = "az provider show --namespace Microsoft.Sql --query registrationState"
        result = self.run_az_command(command)
        
        if result:
            status = result.strip('"')
            print(f"📊 Provider status: {status}")
            
            if status == "Registered":
                return True
            elif status == "Registering":
                print("⏳ Provider is still registering. Waiting...")
                return False
            else:
                print("🔄 Registering Microsoft.Sql provider...")
                self.run_az_command("az provider register --namespace Microsoft.Sql")
                return False
        
        return False

    def wait_for_provider_registration(self, max_wait_minutes=10):
        """Wait for Microsoft.Sql provider to be registered"""
        print(f"⏳ Waiting for Microsoft.Sql provider registration (max {max_wait_minutes} minutes)...")
        
        for i in range(max_wait_minutes * 6):  # Check every 10 seconds
            if self.check_provider_registration():
                print("✅ Microsoft.Sql provider is registered!")
                return True
            
            if i < (max_wait_minutes * 6) - 1:
                print(f"⏳ Still waiting... ({i//6 + 1}/{max_wait_minutes} minutes)")
                time.sleep(10)
        
        print("❌ Timeout waiting for provider registration")
        return False

    def check_resource_group(self):
        """Check if resource group exists"""
        print(f"🔍 Checking resource group: {self.resource_group}")
        
        command = f"az group show --name {self.resource_group}"
        result = self.run_az_command(command)
        
        if result:
            print("✅ Resource group exists")
            return True
        else:
            print(f"❌ Resource group {self.resource_group} not found")
            return False

    def create_sql_server(self):
        """Create Azure SQL Server"""
        print(f"🏗️ Creating SQL Server: {self.server_name}")
        
        # Check if server already exists
        command = f"az sql server show --name {self.server_name} --resource-group {self.resource_group}"
        if self.run_az_command(command):
            print("ℹ️ SQL Server already exists")
            return True
        
        # Create SQL Server
        command = (
            f"az sql server create "
            f"--name {self.server_name} "
            f"--resource-group {self.resource_group} "
            f"--location {self.location} "
            f"--admin-user {self.admin_username} "
            f"--admin-password {self.admin_password}"
        )
        
        result = self.run_az_command(command)
        
        if result:
            print("✅ SQL Server created successfully")
            return True
        else:
            print("❌ Failed to create SQL Server")
            return False

    def configure_firewall(self):
        """Configure SQL Server firewall rules"""
        print("🔥 Configuring firewall rules...")
        
        # Allow Azure services
        command = (
            f"az sql server firewall-rule create "
            f"--resource-group {self.resource_group} "
            f"--server {self.server_name} "
            f"--name AllowAzureServices "
            f"--start-ip-address 0.0.0.0 "
            f"--end-ip-address 0.0.0.0"
        )
        
        if self.run_az_command(command):
            print("✅ Azure services firewall rule created")
        
        # Allow all IPs for development (remove in production)
        command = (
            f"az sql server firewall-rule create "
            f"--resource-group {self.resource_group} "
            f"--server {self.server_name} "
            f"--name AllowAll "
            f"--start-ip-address 0.0.0.0 "
            f"--end-ip-address 255.255.255.255"
        )
        
        if self.run_az_command(command):
            print("✅ Development firewall rule created (allows all IPs)")
            print("⚠️  WARNING: Remove this rule in production!")

    def create_database(self):
        """Create Azure SQL Database"""
        print(f"🗄️ Creating SQL Database: {self.database_name}")
        
        # Check if database already exists
        command = (
            f"az sql db show "
            f"--name {self.database_name} "
            f"--server {self.server_name} "
            f"--resource-group {self.resource_group}"
        )
        
        if self.run_az_command(command):
            print("ℹ️ SQL Database already exists")
            return True
        
        # Create database with Basic tier for development
        command = (
            f"az sql db create "
            f"--name {self.database_name} "
            f"--server {self.server_name} "
            f"--resource-group {self.resource_group} "
            f"--service-objective Basic"
        )
        
        result = self.run_az_command(command)
        
        if result:
            print("✅ SQL Database created successfully")
            return True
        else:
            print("❌ Failed to create SQL Database")
            return False

    def get_connection_info(self):
        """Get connection information"""
        print("📋 Getting connection information...")
        
        # Get server FQDN
        command = (
            f"az sql server show "
            f"--name {self.server_name} "
            f"--resource-group {self.resource_group} "
            f"--query fullyQualifiedDomainName"
        )
        
        server_fqdn = self.run_az_command(command)
        if server_fqdn:
            server_fqdn = server_fqdn.strip('"')
        
        return {
            "server": server_fqdn,
            "database": self.database_name,
            "username": self.admin_username,
            "password": self.admin_password
        }

    def create_env_file(self, connection_info):
        """Create/update .env.database file with Azure SQL settings"""
        print("📝 Creating .env.database.azure file...")
        
        env_content = f"""# Azure SQL Database Configuration
# Production environment for AI Learning Tracker
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# ===============================================
# ENVIRONMENT DETECTION
# ===============================================
ENV=production
ENVIRONMENT=production

# ===============================================
# AZURE SQL DATABASE (PRODUCTION)
# ===============================================
AZURE_SQL_SERVER={connection_info['server']}
AZURE_SQL_DATABASE={connection_info['database']}
AZURE_SQL_USERNAME={connection_info['username']}
AZURE_SQL_PASSWORD={connection_info['password']}

# ===============================================
# ADMIN CONFIGURATION
# ===============================================
ADMIN_PASSWORD=YourSecureAdminPassword123!

# ===============================================
# LOCAL DEVELOPMENT (FALLBACK)
# ===============================================
DATABASE_URL=sqlite:///ai_learning.db
"""
        
        with open('.env.database.azure', 'w') as f:
            f.write(env_content)
        
        print("✅ .env.database.azure file created")

    def test_connection(self, connection_info):
        """Test the database connection"""
        print("🧪 Testing database connection...")
        
        try:
            # Set environment variables for testing
            os.environ['ENV'] = 'production'
            os.environ['AZURE_SQL_SERVER'] = connection_info['server']
            os.environ['AZURE_SQL_DATABASE'] = connection_info['database']
            os.environ['AZURE_SQL_USERNAME'] = connection_info['username']
            os.environ['AZURE_SQL_PASSWORD'] = connection_info['password']
            
            # Import and test our database manager
            from database_environment_manager import DatabaseEnvironmentManager
            
            db_manager = DatabaseEnvironmentManager()
            db_manager.connect_to_database()
            db_manager.create_schema()
            
            if db_manager.test_connection():
                print("✅ Database connection and schema creation successful!")
                db_manager.close_connection()
                return True
            else:
                print("❌ Database connection test failed")
                db_manager.close_connection()
                return False
                
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False

    def run_setup(self):
        """Run the complete Azure SQL setup"""
        print("🚀 Starting Azure SQL Database Setup")
        print("=" * 50)
        
        # Step 1: Check provider registration
        if not self.wait_for_provider_registration():
            print("❌ Setup failed: Microsoft.Sql provider not registered")
            return False
        
        # Step 2: Check resource group
        if not self.check_resource_group():
            print("❌ Setup failed: Resource group not found")
            return False
        
        # Step 3: Create SQL Server
        if not self.create_sql_server():
            print("❌ Setup failed: Could not create SQL Server")
            return False
        
        # Step 4: Configure firewall
        self.configure_firewall()
        
        # Step 5: Create database
        if not self.create_database():
            print("❌ Setup failed: Could not create SQL Database")
            return False
        
        # Step 6: Get connection info
        connection_info = self.get_connection_info()
        if not connection_info['server']:
            print("❌ Setup failed: Could not get connection information")
            return False
        
        # Step 7: Create environment file
        self.create_env_file(connection_info)
        
        # Step 8: Test connection
        print("\n⏳ Waiting 30 seconds for database to be ready...")
        time.sleep(30)
        
        if self.test_connection(connection_info):
            print("\n🎉 Azure SQL Database setup completed successfully!")
            print("\n📋 Connection Details:")
            print(f"   Server: {connection_info['server']}")
            print(f"   Database: {connection_info['database']}")
            print(f"   Username: {connection_info['username']}")
            print("   Password: [STORED IN .env.database.azure]")
            print("\n📝 Next Steps:")
            print("   1. Copy .env.database.azure to .env.database for production use")
            print("   2. Update your Azure App Service with these environment variables")
            print("   3. Deploy your application to Azure")
            return True
        else:
            print("❌ Setup completed but connection test failed")
            print("   The database may need more time to initialize")
            return False


def main():
    """Main execution"""
    setup = AzureSQLSetup()
    
    if setup.run_setup():
        print("\n✅ Azure SQL Database setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Azure SQL Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
