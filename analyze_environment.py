#!/usr/bin/env python3
"""
Environment Variable Analysis and Validation Tool
Analyzes all environment variables used in app.py and validates their presence
"""

import os
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class EnvType(Enum):
    REQUIRED_AZURE = "Required for Azure"
    REQUIRED_LOCAL = "Required for Local"
    REQUIRED_BOTH = "Required for Both"
    OPTIONAL_AZURE = "Optional for Azure"
    OPTIONAL_LOCAL = "Optional for Local"
    OPTIONAL_BOTH = "Optional for Both"

@dataclass
class EnvVar:
    name: str
    type: EnvType
    default_value: str = None
    description: str = ""
    current_value: str = None
    is_set: bool = False

class EnvironmentAnalyzer:
    def __init__(self):
        self.env_vars: Dict[str, EnvVar] = {}
        self._define_environment_variables()
        self._load_current_values()
    
    def _define_environment_variables(self):
        """Define all environment variables used in app.py"""
        
        # === CORE APPLICATION VARIABLES ===
        self.env_vars['SECRET_KEY'] = EnvVar(
            name='SECRET_KEY',
            type=EnvType.REQUIRED_BOTH,
            default_value='auto-generated',
            description='Flask session secret key for security'
        )
        
        self.env_vars['ADMIN_PASSWORD'] = EnvVar(
            name='ADMIN_PASSWORD',
            type=EnvType.REQUIRED_BOTH,
            description='Password for admin user (NO FALLBACK)'
        )
        
        # === DATABASE CONFIGURATION ===
        self.env_vars['DATABASE_PATH'] = EnvVar(
            name='DATABASE_PATH',
            type=EnvType.OPTIONAL_LOCAL,
            default_value='ai_learning.db',
            description='SQLite database file path for local development'
        )
        
        # === AZURE SQL CONFIGURATION ===
        self.env_vars['AZURE_SQL_SERVER'] = EnvVar(
            name='AZURE_SQL_SERVER',
            type=EnvType.REQUIRED_AZURE,
            description='Azure SQL Server hostname (e.g., server.database.windows.net)'
        )
        
        self.env_vars['AZURE_SQL_DATABASE'] = EnvVar(
            name='AZURE_SQL_DATABASE',
            type=EnvType.REQUIRED_AZURE,
            description='Azure SQL Database name'
        )
        
        self.env_vars['AZURE_SQL_USERNAME'] = EnvVar(
            name='AZURE_SQL_USERNAME',
            type=EnvType.REQUIRED_AZURE,
            description='Azure SQL Database username'
        )
        
        self.env_vars['AZURE_SQL_PASSWORD'] = EnvVar(
            name='AZURE_SQL_PASSWORD',
            type=EnvType.REQUIRED_AZURE,
            description='Azure SQL Database password'
        )
        
        # === APPLICATION RUNTIME ===
        self.env_vars['PORT'] = EnvVar(
            name='PORT',
            type=EnvType.OPTIONAL_AZURE,
            default_value='5000',
            description='Port for Flask application (Azure sets this automatically)'
        )
        
        self.env_vars['FLASK_ENV'] = EnvVar(
            name='FLASK_ENV',
            type=EnvType.OPTIONAL_BOTH,
            default_value='development',
            description='Flask environment (production/development)'
        )
        
        # === ADDITIONAL VARIABLES FROM TEMPLATES ===
        self.env_vars['FLASK_DEBUG'] = EnvVar(
            name='FLASK_DEBUG',
            type=EnvType.OPTIONAL_BOTH,
            default_value='False',
            description='Flask debug mode setting'
        )
        
        self.env_vars['DEMO_USERNAME'] = EnvVar(
            name='DEMO_USERNAME',
            type=EnvType.OPTIONAL_BOTH,
            default_value='demo',
            description='Demo user username for testing'
        )
        
        self.env_vars['DEMO_PASSWORD'] = EnvVar(
            name='DEMO_PASSWORD',
            type=EnvType.OPTIONAL_BOTH,
            description='Demo user password for testing'
        )
        
        self.env_vars['AZURE_STORAGE_CONNECTION_STRING'] = EnvVar(
            name='AZURE_STORAGE_CONNECTION_STRING',
            type=EnvType.OPTIONAL_AZURE,
            description='Azure Storage connection string for backup system'
        )
    
    def _load_current_values(self):
        """Load current values from environment"""
        for var_name, env_var in self.env_vars.items():
            env_var.current_value = os.environ.get(var_name)
            env_var.is_set = env_var.current_value is not None
    
    def is_azure_environment(self) -> bool:
        """Detect if we're in Azure environment based on Azure SQL variables"""
        azure_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
        return all(self.env_vars[var].is_set for var in azure_vars)
    
    def is_local_environment(self) -> bool:
        """Detect if we're in local environment"""
        return not self.is_azure_environment()
    
    def get_required_for_current_env(self) -> List[EnvVar]:
        """Get variables required for current environment"""
        is_azure = self.is_azure_environment()
        required_vars = []
        
        for env_var in self.env_vars.values():
            if env_var.type in [EnvType.REQUIRED_BOTH]:
                required_vars.append(env_var)
            elif is_azure and env_var.type == EnvType.REQUIRED_AZURE:
                required_vars.append(env_var)
            elif not is_azure and env_var.type == EnvType.REQUIRED_LOCAL:
                required_vars.append(env_var)
        
        return required_vars
    
    def get_missing_required(self) -> List[EnvVar]:
        """Get missing required variables for current environment"""
        required = self.get_required_for_current_env()
        return [var for var in required if not var.is_set]
    
    def get_optional_for_current_env(self) -> List[EnvVar]:
        """Get optional variables for current environment"""
        is_azure = self.is_azure_environment()
        optional_vars = []
        
        for env_var in self.env_vars.values():
            if env_var.type in [EnvType.OPTIONAL_BOTH]:
                optional_vars.append(env_var)
            elif is_azure and env_var.type == EnvType.OPTIONAL_AZURE:
                optional_vars.append(env_var)
            elif not is_azure and env_var.type == EnvType.OPTIONAL_LOCAL:
                optional_vars.append(env_var)
        
        return optional_vars
    
    def generate_report(self) -> str:
        """Generate comprehensive environment variable report"""
        is_azure = self.is_azure_environment()
        env_type = "Azure/Production" if is_azure else "Local/Development"
        
        report = [
            "=" * 80,
            "ENVIRONMENT VARIABLE ANALYSIS REPORT",
            "=" * 80,
            f"Detected Environment: {env_type}",
            f"Analysis Date: {os.getcwd()}",
            "",
            "🔍 DETECTION LOGIC:",
            "- Azure Environment: All 4 AZURE_SQL_* variables are set",
            "- Local Environment: Missing any AZURE_SQL_* variables",
            ""
        ]
        
        # Required Variables Analysis
        required_vars = self.get_required_for_current_env()
        missing_required = self.get_missing_required()
        
        report.extend([
            f"📋 REQUIRED VARIABLES FOR {env_type.upper()} ({len(required_vars)} total):",
            "-" * 60
        ])
        
        for var in required_vars:
            status = "✅ SET" if var.is_set else "❌ MISSING"
            value_display = "[HIDDEN]" if "PASSWORD" in var.name else (var.current_value or "None")
            default_info = f" (default: {var.default_value})" if var.default_value else ""
            
            report.append(f"{status} {var.name}: {value_display}{default_info}")
            if var.description:
                report.append(f"     Description: {var.description}")
            report.append("")
        
        # Optional Variables Analysis
        optional_vars = self.get_optional_for_current_env()
        report.extend([
            f"⚙️ OPTIONAL VARIABLES FOR {env_type.upper()} ({len(optional_vars)} total):",
            "-" * 60
        ])
        
        for var in optional_vars:
            status = "✅ SET" if var.is_set else "⚪ NOT SET"
            value_display = "[HIDDEN]" if "PASSWORD" in var.name else (var.current_value or "None")
            default_info = f" (default: {var.default_value})" if var.default_value else ""
            
            report.append(f"{status} {var.name}: {value_display}{default_info}")
            if var.description:
                report.append(f"     Description: {var.description}")
            report.append("")
        
        # Critical Issues
        if missing_required:
            report.extend([
                "🚨 CRITICAL ISSUES:",
                "-" * 60
            ])
            for var in missing_required:
                report.append(f"❌ MISSING REQUIRED: {var.name}")
                report.append(f"   Description: {var.description}")
                report.append(f"   Impact: Application may fail to start or function properly")
                report.append("")
        
        # Environment-Specific Recommendations
        report.extend([
            "💡 RECOMMENDATIONS:",
            "-" * 60
        ])
        
        if is_azure:
            report.extend([
                "Azure/Production Environment Detected:",
                "1. ✅ All Azure SQL variables are configured",
                "2. 🔍 Verify Azure App Service configuration matches these values",
                "3. 🔐 Ensure passwords are secure and rotated regularly",
                "4. 📊 Monitor Azure SQL performance and costs",
                ""
            ])
        else:
            report.extend([
                "Local/Development Environment Detected:",
                "1. 🔍 SQLite database will be used for local development",
                "2. 📁 Database file location: " + os.environ.get('DATABASE_PATH', 'ai_learning.db'),
                "3. 🔧 To test Azure SQL locally, set all AZURE_SQL_* variables",
                "4. 📋 Use .env.azure.template for Azure configuration",
                ""
            ])
        
        # Missing Variables Impact
        if missing_required:
            report.extend([
                "⚠️ IMPACT OF MISSING VARIABLES:",
                "-" * 60
            ])
            for var in missing_required:
                if var.name == 'ADMIN_PASSWORD':
                    report.append("❌ ADMIN_PASSWORD missing: Admin user creation will FAIL")
                elif 'AZURE_SQL' in var.name:
                    report.append(f"❌ {var.name} missing: Azure SQL connection will FAIL")
                report.append("")
        
        # Configuration Files Status
        report.extend([
            "📁 CONFIGURATION FILES STATUS:",
            "-" * 60
        ])
        
        config_files = [
            ('.env', 'Main environment file'),
            ('.env.template', 'Template for main configuration'),
            ('.env.azure', 'Azure-specific configuration'),
            ('.env.azure.template', 'Template for Azure configuration'),
            ('.env.database', 'Database-specific configuration'),
            ('.env.database.template', 'Template for database configuration')
        ]
        
        for filename, description in config_files:
            exists = os.path.exists(filename)
            status = "✅ EXISTS" if exists else "❌ MISSING"
            report.append(f"{status} {filename}: {description}")
        
        report.extend([
            "",
            "=" * 80,
            "END OF ANALYSIS",
            "=" * 80
        ])
        
        return "\n".join(report)
    
    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Validate current environment and return status and issues"""
        issues = []
        
        # Check for missing required variables
        missing_required = self.get_missing_required()
        for var in missing_required:
            issues.append(f"Missing required variable: {var.name}")
        
        # Check for critical security issues
        if self.env_vars['ADMIN_PASSWORD'].is_set:
            admin_pass = self.env_vars['ADMIN_PASSWORD'].current_value
            if admin_pass and len(admin_pass) < 8:
                issues.append("ADMIN_PASSWORD is too short (minimum 8 characters)")
        
        # Check Azure SQL configuration consistency
        if self.is_azure_environment():
            azure_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
            set_azure_vars = [var for var in azure_vars if self.env_vars[var].is_set]
            if len(set_azure_vars) > 0 and len(set_azure_vars) < 4:
                issues.append(f"Partial Azure SQL configuration: {len(set_azure_vars)}/4 variables set")
        
        return len(issues) == 0, issues

def main():
    """Main function to run the analysis"""
    analyzer = EnvironmentAnalyzer()
    
    # Generate and print report
    report = analyzer.generate_report()
    print(report)
    
    # Validate environment
    is_valid, issues = analyzer.validate_environment()
    
    if not is_valid:
        print("\n🚨 ENVIRONMENT VALIDATION FAILED:")
        for issue in issues:
            print(f"   ❌ {issue}")
        print("\n💡 Fix these issues before running the application.")
        return 1
    else:
        print("\n✅ ENVIRONMENT VALIDATION PASSED")
        print("   All required variables are properly configured.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
