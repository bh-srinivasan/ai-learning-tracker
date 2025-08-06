#!/usr/bin/env python3
"""
Enhanced Environment Variable Analysis for AI Learning Tracker
Properly handles Azure Portal Application Settings vs Local .env files
"""

import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class EnvironmentType(Enum):
    LOCAL = "LOCAL"
    AZURE = "AZURE" 
    PARTIAL_AZURE = "PARTIAL_AZURE"
    UNKNOWN = "UNKNOWN"

class VariableSource(Enum):
    LOCAL_ENV_FILE = "Local .env File"
    AZURE_PORTAL = "Azure Portal Application Settings"
    SYSTEM_ENV = "System Environment"
    NOT_SET = "Not Set"

@dataclass
class EnvironmentVariable:
    name: str
    required_local: bool
    required_azure: bool
    description: str
    current_value: Optional[str] = None
    source: VariableSource = VariableSource.NOT_SET
    is_set: bool = False

class EnvironmentAnalyzer:
    def __init__(self):
        """Initialize environment analyzer with comprehensive variable definitions"""
        self.variables = self._define_all_variables()
        self.env_type = self._detect_environment_type()
        self._load_current_values()
    
    def _define_all_variables(self) -> Dict[str, EnvironmentVariable]:
        """Define all environment variables with context-specific requirements"""
        return {
            # === CORE APPLICATION SECURITY ===
            'SECRET_KEY': EnvironmentVariable(
                name='SECRET_KEY',
                required_local=True,
                required_azure=True,
                description='Flask session secret key (CRITICAL for security)'
            ),
            
            'ADMIN_PASSWORD': EnvironmentVariable(
                name='ADMIN_PASSWORD',
                required_local=True,
                required_azure=True,
                description='Admin user password (NO fallback allowed)'
            ),
            
            # === AZURE SQL CONFIGURATION (Azure Only) ===
            'AZURE_SQL_SERVER': EnvironmentVariable(
                name='AZURE_SQL_SERVER',
                required_local=False,
                required_azure=True,
                description='Azure SQL Server hostname (e.g., server.database.windows.net)'
            ),
            
            'AZURE_SQL_DATABASE': EnvironmentVariable(
                name='AZURE_SQL_DATABASE',
                required_local=False,
                required_azure=True,
                description='Azure SQL Database name'
            ),
            
            'AZURE_SQL_USERNAME': EnvironmentVariable(
                name='AZURE_SQL_USERNAME',
                required_local=False,
                required_azure=True,
                description='Azure SQL Database username'
            ),
            
            'AZURE_SQL_PASSWORD': EnvironmentVariable(
                name='AZURE_SQL_PASSWORD',
                required_local=False,
                required_azure=True,
                description='Azure SQL Database password'
            ),
            
            # === OPTIONAL CONFIGURATION ===
            'DATABASE_PATH': EnvironmentVariable(
                name='DATABASE_PATH',
                required_local=False,
                required_azure=False,
                description='SQLite database file path (Local only)'
            ),
            
            'PORT': EnvironmentVariable(
                name='PORT',
                required_local=False,
                required_azure=False,
                description='Application port (Azure sets automatically)'
            ),
            
            'FLASK_ENV': EnvironmentVariable(
                name='FLASK_ENV',
                required_local=False,
                required_azure=False,
                description='Flask environment mode (development/production)'
            ),
            
            'FLASK_DEBUG': EnvironmentVariable(
                name='FLASK_DEBUG',
                required_local=False,
                required_azure=False,
                description='Flask debug mode setting'
            ),
            
            'DEMO_PASSWORD': EnvironmentVariable(
                name='DEMO_PASSWORD',
                required_local=False,
                required_azure=False,
                description='Demo user password for testing'
            ),
            
            'AZURE_STORAGE_CONNECTION_STRING': EnvironmentVariable(
                name='AZURE_STORAGE_CONNECTION_STRING',
                required_local=False,
                required_azure=False,
                description='Azure Storage connection for file backup'
            )
        }
    
    def _detect_environment_type(self) -> EnvironmentType:
        """Detect environment type with enhanced Azure detection"""
        # Check for Azure App Service specific environment variables
        azure_indicators = [
            'WEBSITE_SITE_NAME',           # Azure App Service
            'AZURE_FUNCTIONS_ENVIRONMENT', # Azure Functions
            'WEBSITE_RESOURCE_GROUP',      # Azure Resource Group
            'WEBSITE_OWNER_NAME'           # Azure Subscription
        ]
        
        has_azure_indicators = any(os.environ.get(var) for var in azure_indicators)
        
        # Check for Azure SQL configuration
        azure_sql_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
        azure_sql_count = sum(1 for var in azure_sql_vars if os.environ.get(var))
        
        if has_azure_indicators or azure_sql_count == 4:
            return EnvironmentType.AZURE
        elif azure_sql_count == 0:
            return EnvironmentType.LOCAL
        elif 0 < azure_sql_count < 4:
            return EnvironmentType.PARTIAL_AZURE
        else:
            return EnvironmentType.UNKNOWN
    
    def _load_current_values(self):
        """Load current values and determine their source"""
        # Load .env file for local environment
        if self.env_type == EnvironmentType.LOCAL:
            self._load_dotenv_file()
        
        # Load current values from environment
        for var_name, var_obj in self.variables.items():
            value = os.environ.get(var_name)
            var_obj.current_value = value
            var_obj.is_set = value is not None and value.strip() != ''
            
            # Determine variable source
            if var_obj.is_set:
                if self.env_type == EnvironmentType.AZURE:
                    var_obj.source = VariableSource.AZURE_PORTAL
                elif self.env_type == EnvironmentType.LOCAL and self._is_in_dotenv(var_name):
                    var_obj.source = VariableSource.LOCAL_ENV_FILE
                else:
                    var_obj.source = VariableSource.SYSTEM_ENV
            else:
                var_obj.source = VariableSource.NOT_SET
    
    def _load_dotenv_file(self):
        """Load .env file if it exists"""
        env_path = '.env'
        if os.path.exists(env_path):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
                print(f"✅ Loaded local environment from {env_path}")
            except ImportError:
                print(f"⚠️ python-dotenv not installed, .env file not loaded")
        else:
            print(f"⚠️ No .env file found at {env_path}")
    
    def _is_in_dotenv(self, var_name: str) -> bool:
        """Check if variable is defined in .env file"""
        env_path = '.env'
        if not os.path.exists(env_path):
            return False
        
        try:
            with open(env_path, 'r') as f:
                content = f.read()
                return f'{var_name}=' in content
        except:
            return False
    
    def check_variable_naming_issues(self) -> List[Dict[str, str]]:
        """Check for common variable naming mismatches"""
        issues = []
        
        # Check for FLASK_SECRET_KEY vs SECRET_KEY mismatch
        if os.environ.get('FLASK_SECRET_KEY') and not os.environ.get('SECRET_KEY'):
            issues.append({
                'type': 'NAMING_MISMATCH',
                'issue': 'FLASK_SECRET_KEY is set but app.py expects SECRET_KEY',
                'current': 'FLASK_SECRET_KEY',
                'expected': 'SECRET_KEY',
                'solution': 'Rename FLASK_SECRET_KEY to SECRET_KEY in your configuration'
            })
        
        return issues
    
    def get_required_variables(self) -> List[EnvironmentVariable]:
        """Get variables required for current environment"""
        required = []
        for var in self.variables.values():
            if self.env_type == EnvironmentType.AZURE and var.required_azure:
                required.append(var)
            elif self.env_type == EnvironmentType.LOCAL and var.required_local:
                required.append(var)
        return required
    
    def get_missing_required(self) -> List[EnvironmentVariable]:
        """Get required variables that are missing"""
        required = self.get_required_variables()
        return [var for var in required if not var.is_set]
    
    def check_local_configuration_files(self) -> Dict[str, str]:
        """Check status of local configuration files"""
        config_files = {
            '.env': 'Main environment file',
            '.env.template': 'Template for local development',
            '.env.azure': 'Azure-specific configuration',
            '.env.azure.template': 'Template for Azure deployment',
            '.env.database': 'Database-specific configuration',
            '.env.database.template': 'Template for database settings'
        }
        
        status = {}
        for file_name, description in config_files.items():
            if os.path.exists(file_name):
                status[file_name] = f"✅ EXISTS - {description}"
            else:
                status[file_name] = f"❌ MISSING - {description}"
        
        return status
    
    def get_azure_environment_info(self) -> Dict[str, str]:
        """Get Azure-specific environment information"""
        azure_info = {}
        azure_vars = [
            'WEBSITE_SITE_NAME',
            'WEBSITE_RESOURCE_GROUP', 
            'WEBSITE_OWNER_NAME',
            'AZURE_FUNCTIONS_ENVIRONMENT',
            'WEBSITE_SKU',
            'WEBSITE_HOSTNAME'
        ]
        
        for var in azure_vars:
            value = os.environ.get(var)
            azure_info[var] = value if value else 'Not Set'
        
        return azure_info
    
    def analyze_comprehensive(self) -> Dict:
        """Perform comprehensive environment analysis"""
        print(f"\n🔍 COMPREHENSIVE ENVIRONMENT ANALYSIS")
        print(f"{'='*80}")
        
        # Environment Detection
        print(f"Environment Type: {self.env_type.value}")
        
        if self.env_type == EnvironmentType.AZURE:
            print(f"Configuration Source: Azure Portal > App Service > Configuration > Application Settings")
            azure_info = self.get_azure_environment_info()
            print(f"\n🌐 AZURE ENVIRONMENT DETAILS:")
            for key, value in azure_info.items():
                if value != 'Not Set':
                    print(f"  {key}: {value}")
        
        elif self.env_type == EnvironmentType.LOCAL:
            print(f"Configuration Source: Local .env files")
            config_status = self.check_local_configuration_files()
            print(f"\n📁 LOCAL CONFIGURATION FILES:")
            for file_name, status in config_status.items():
                print(f"  {status}")
        
        # Variable Naming Issues
        naming_issues = self.check_variable_naming_issues()
        if naming_issues:
            print(f"\n⚠️ VARIABLE NAMING ISSUES:")
            for issue in naming_issues:
                print(f"  ISSUE: {issue['issue']}")
                print(f"  SOLUTION: {issue['solution']}")
        
        # Variables Analysis
        print(f"\n📋 ENVIRONMENT VARIABLES STATUS:")
        print(f"{'Variable':<30} | {'Status':<10} | {'Required':<8} | {'Source':<25} | {'Description'}")
        print(f"{'-'*30} | {'-'*10} | {'-'*8} | {'-'*25} | {'-'*30}")
        
        for var_name, var_obj in self.variables.items():
            is_required = (self.env_type == EnvironmentType.AZURE and var_obj.required_azure) or \
                         (self.env_type == EnvironmentType.LOCAL and var_obj.required_local)
            
            status = "✅ SET" if var_obj.is_set else "❌ MISSING"
            required = "REQUIRED" if is_required else "OPTIONAL"
            source = var_obj.source.value
            
            print(f"{var_name:<30} | {status:<10} | {required:<8} | {source:<25} | {var_obj.description}")
        
        # Summary
        missing_required = self.get_missing_required()
        total_vars = len(self.variables)
        set_vars = sum(1 for var in self.variables.values() if var.is_set)
        required_vars = len(self.get_required_variables())
        
        print(f"\n📊 SUMMARY:")
        print(f"{'='*80}")
        print(f"Environment: {self.env_type.value}")
        print(f"Total Variables: {total_vars}")
        print(f"Variables Set: {set_vars}")
        print(f"Required for {self.env_type.value}: {required_vars}")
        print(f"Missing Required: {len(missing_required)}")
        
        if missing_required:
            print(f"\n🚨 CRITICAL MISSING VARIABLES:")
            for var in missing_required:
                print(f"  - {var.name}: {var.description}")
            
            if self.env_type == EnvironmentType.LOCAL:
                print(f"\n💡 RESOLUTION FOR LOCAL ENVIRONMENT:")
                print(f"  1. Add missing variables to .env file")
                print(f"  2. Check variable naming (FLASK_SECRET_KEY should be SECRET_KEY)")
                print(f"  3. Restart the application after updating .env")
            
            elif self.env_type == EnvironmentType.AZURE:
                print(f"\n💡 RESOLUTION FOR AZURE ENVIRONMENT:")
                print(f"  1. Open Azure Portal")
                print(f"  2. Navigate to your App Service")
                print(f"  3. Go to Configuration > Application Settings")
                print(f"  4. Add the missing environment variables")
                print(f"  5. Save and restart the app service")
        
        validation_passed = len(missing_required) == 0
        print(f"\n🎯 OVERALL VALIDATION: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
        
        if not validation_passed:
            print(f"⚠️ Application may not function correctly until missing variables are configured!")
        
        return {
            'environment_type': self.env_type.value,
            'validation_passed': validation_passed,
            'missing_required': [var.name for var in missing_required],
            'naming_issues': naming_issues,
            'total_variables': total_vars,
            'set_variables': set_vars,
            'azure_info': self.get_azure_environment_info() if self.env_type == EnvironmentType.AZURE else None
        }

def main():
    """Main function to run the analysis"""
    print("🚀 Starting Enhanced Environment Analysis...")
    
    try:
        # Load .env file first for local development
        if os.path.exists('.env'):
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass
        
        analyzer = EnvironmentAnalyzer()
        result = analyzer.analyze_comprehensive()
        
        print(f"\n✅ Analysis completed successfully!")
        return result
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
