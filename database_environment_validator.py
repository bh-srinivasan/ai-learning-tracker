"""
Database Environment Validator
============================

This module provides comprehensive validation and logging for dual-environment
database functionality, ensuring seamless operation between local development
and Azure production environments.

Features:
- Environment detection (local vs Azure/cloud)
- Database connection validation
- User creation testing with environment-specific logging
- Azure Storage sync status verification
- Connection string validation
- Database host identification
"""

import os
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
import platform
import socket
from typing import Dict, Any, Tuple, Optional
from azure.storage.blob import BlobServiceClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseEnvironmentValidator:
    """Validates database functionality across development and production environments"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.database_path = self._get_database_path()
        self.azure_enabled = self._check_azure_storage_availability()
        self.validation_results = {}
        
    def _detect_environment(self) -> str:
        """Detect current environment (local/development vs Azure/production)"""
        # Check for Azure App Service environment variables
        if os.getenv('WEBSITE_SITE_NAME'):
            return 'azure_production'
        elif os.getenv('WEBSITE_INSTANCE_ID'):
            return 'azure_staging' 
        elif os.getenv('FLASK_ENV') == 'production':
            return 'production'
        elif os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            return 'ci_testing'
        else:
            return 'local_development'
    
    def _get_database_path(self) -> str:
        """Get database path based on environment"""
        database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_learning.db')
        if database_url.startswith('sqlite:///'):
            return database_url.replace('sqlite:///', '')
        return 'ai_learning.db'
    
    def _check_azure_storage_availability(self) -> bool:
        """Check if Azure Storage is configured and available"""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        return connection_string is not None and connection_string.strip() != ''
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive environment information"""
        info = {
            'environment': self.environment,
            'database_path': self.database_path,
            'database_exists': os.path.exists(self.database_path),
            'database_size_bytes': os.path.getsize(self.database_path) if os.path.exists(self.database_path) else 0,
            'azure_storage_enabled': self.azure_enabled,
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname()
            },
            'environment_variables': {
                'FLASK_ENV': os.getenv('FLASK_ENV', 'not_set'),
                'FLASK_DEBUG': os.getenv('FLASK_DEBUG', 'not_set'),
                'WEBSITE_SITE_NAME': os.getenv('WEBSITE_SITE_NAME', 'not_set'),
                'WEBSITE_INSTANCE_ID': os.getenv('WEBSITE_INSTANCE_ID', 'not_set'),
                'DATABASE_URL': os.getenv('DATABASE_URL', 'not_set'),
                'AZURE_STORAGE_CONNECTION_STRING': 'configured' if self.azure_enabled else 'not_configured'
            }
        }
        
        # Add Azure-specific info if available
        if self.environment.startswith('azure'):
            info['azure_info'] = {
                'site_name': os.getenv('WEBSITE_SITE_NAME'),
                'resource_group': os.getenv('WEBSITE_RESOURCE_GROUP'),
                'subscription_id': os.getenv('WEBSITE_OWNER_NAME'),
                'instance_id': os.getenv('WEBSITE_INSTANCE_ID'),
                'hostname': os.getenv('WEBSITE_HOSTNAME')
            }
        
        return info
    
    def test_database_connection(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test database connection and gather connection details"""
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            
            # Test basic operations
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get user count if users table exists
            user_count = 0
            if 'users' in tables:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
            
            # Get database file info
            db_info = {
                'path': os.path.abspath(self.database_path),
                'size_bytes': os.path.getsize(self.database_path) if os.path.exists(self.database_path) else 0,
                'tables': tables,
                'user_count': user_count,
                'writable': os.access(os.path.dirname(os.path.abspath(self.database_path)), os.W_OK),
                'connection_successful': True
            }
            
            conn.close()
            return True, "Database connection successful", db_info
            
        except Exception as e:
            error_msg = f"Database connection failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {'connection_successful': False, 'error': str(e)}
    
    def test_user_creation(self, test_username: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Test user creation functionality with environment logging"""
        if test_username is None:
            test_username = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_results = {
            'test_username': test_username,
            'creation_timestamp': datetime.now().isoformat(),
            'environment': self.environment,
            'database_path': self.database_path
        }
        
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cursor.fetchone():
                test_results['error'] = "Users table does not exist"
                conn.close()
                return False, "Users table does not exist", test_results
            
            # Create test user
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash("test_password_123")
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, level, points, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (test_username, password_hash, 'Beginner', 0, 'active', datetime.now()))
            
            conn.commit()
            user_id = cursor.lastrowid
            test_results['user_id'] = user_id
            
            # Verify user was created
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            created_user = cursor.fetchone()
            
            if created_user:
                test_results['verification'] = {
                    'user_found': True,
                    'username': created_user['username'],
                    'level': created_user['level'],
                    'points': created_user['points'],
                    'status': created_user['status'],
                    'created_at': created_user['created_at']
                }
                
                # Clean up - delete test user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                test_results['cleanup_completed'] = True
                
            conn.close()
            
            success_msg = f"User creation test successful in {self.environment} environment"
            logger.info(success_msg)
            logger.info(f"Database host: {os.path.abspath(self.database_path)}")
            logger.info(f"Test user '{test_username}' created and verified successfully")
            
            return True, success_msg, test_results
            
        except Exception as e:
            error_msg = f"User creation test failed: {str(e)}"
            test_results['error'] = str(e)
            logger.error(error_msg)
            return False, error_msg, test_results
    
    def test_azure_storage_sync(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test Azure Storage connectivity and sync functionality"""
        sync_results = {
            'azure_enabled': self.azure_enabled,
            'environment': self.environment,
            'test_timestamp': datetime.now().isoformat()
        }
        
        if not self.azure_enabled:
            return True, "Azure Storage not configured - running in local-only mode", sync_results
        
        try:
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # Test connectivity by listing containers
            containers = list(blob_service_client.list_containers())
            sync_results['containers'] = [container.name for container in containers]
            
            # Test container access
            container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'database')
            container_client = blob_service_client.get_container_client(container_name)
            
            try:
                container_properties = container_client.get_container_properties()
                sync_results['container_info'] = {
                    'name': container_name,
                    'exists': True,
                    'last_modified': container_properties.last_modified.isoformat() if container_properties.last_modified else None
                }
            except Exception as e:
                sync_results['container_info'] = {
                    'name': container_name,
                    'exists': False,
                    'error': str(e)
                }
            
            success_msg = "Azure Storage connectivity test successful"
            logger.info(success_msg)
            return True, success_msg, sync_results
            
        except Exception as e:
            error_msg = f"Azure Storage test failed: {str(e)}"
            sync_results['error'] = str(e)
            logger.error(error_msg)
            return False, error_msg, sync_results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests and return comprehensive results"""
        logger.info("=" * 80)
        logger.info("🔍 DATABASE ENVIRONMENT VALIDATION STARTED")
        logger.info("=" * 80)
        
        validation_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'environment_info': self.get_environment_info(),
            'tests': {}
        }
        
        # Log environment detection
        env_info = validation_results['environment_info']
        logger.info(f"🌍 Environment detected: {env_info['environment']}")
        logger.info(f"📂 Database path: {env_info['database_path']}")
        logger.info(f"🏠 Hostname: {env_info['platform']['hostname']}")
        logger.info(f"💾 Platform: {env_info['platform']['system']} {env_info['platform']['release']}")
        logger.info(f"☁️ Azure Storage: {'✅ Enabled' if env_info['azure_storage_enabled'] else '❌ Disabled'}")
        
        # Test 1: Database Connection
        logger.info("\n📡 Testing database connection...")
        conn_success, conn_msg, conn_details = self.test_database_connection()
        validation_results['tests']['database_connection'] = {
            'success': conn_success,
            'message': conn_msg,
            'details': conn_details
        }
        
        if conn_success:
            logger.info(f"✅ {conn_msg}")
            logger.info(f"📊 Database info: {conn_details['size_bytes']} bytes, {len(conn_details['tables'])} tables, {conn_details['user_count']} users")
        else:
            logger.error(f"❌ {conn_msg}")
        
        # Test 2: User Creation
        logger.info("\n👤 Testing user creation functionality...")
        user_success, user_msg, user_details = self.test_user_creation()
        validation_results['tests']['user_creation'] = {
            'success': user_success,
            'message': user_msg,
            'details': user_details
        }
        
        if user_success:
            logger.info(f"✅ {user_msg}")
        else:
            logger.error(f"❌ {user_msg}")
        
        # Test 3: Azure Storage Sync
        logger.info("\n☁️ Testing Azure Storage sync functionality...")
        azure_success, azure_msg, azure_details = self.test_azure_storage_sync()
        validation_results['tests']['azure_storage'] = {
            'success': azure_success,
            'message': azure_msg,
            'details': azure_details
        }
        
        if azure_success:
            logger.info(f"✅ {azure_msg}")
        else:
            logger.warning(f"⚠️ {azure_msg}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📋 VALIDATION SUMMARY")
        logger.info("=" * 80)
        
        all_tests_passed = all(test['success'] for test in validation_results['tests'].values())
        validation_results['overall_success'] = all_tests_passed
        
        for test_name, test_result in validation_results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            logger.info(f"{status} {test_name.replace('_', ' ').title()}: {test_result['message']}")
        
        logger.info(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if all_tests_passed else '⚠️ SOME TESTS FAILED'}")
        logger.info("=" * 80)
        
        return validation_results

def validate_dual_environment_database():
    """Main function to validate dual-environment database functionality"""
    validator = DatabaseEnvironmentValidator()
    return validator.run_comprehensive_validation()

if __name__ == "__main__":
    # Run validation when script is executed directly
    results = validate_dual_environment_database()
    
    # Print summary
    print("\n🔍 DATABASE ENVIRONMENT VALIDATION COMPLETE")
    print(f"Environment: {results['environment_info']['environment']}")
    print(f"Database: {results['environment_info']['database_path']}")
    print(f"Azure Storage: {'Enabled' if results['environment_info']['azure_storage_enabled'] else 'Disabled'}")
    print(f"Overall Success: {results['overall_success']}")
