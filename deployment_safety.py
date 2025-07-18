"""
Deployment Safety Integration for Flask App
===========================================

Integrates data integrity monitoring and backup systems into the Flask application
to ensure safe deployments and data protection.
"""

import os
import sys
import logging
from datetime import datetime
from flask import current_app
import atexit
import signal

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_integrity_monitor import DataIntegrityMonitor, run_pre_deployment_check, run_post_deployment_check
from azure_backup_system import AzureBackupManager, BackupScheduler

logger = logging.getLogger('DeploymentSafety')

class DeploymentSafetyManager:
    """
    Manages deployment safety for the Flask application
    """
    
    def __init__(self, app=None):
        self.app = app
        self.integrity_monitor = None
        self.backup_manager = None
        self.backup_scheduler = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Initialize monitoring systems
        self.integrity_monitor = DataIntegrityMonitor()
        
        # Initialize backup system if Azure storage is configured
        azure_connection = app.config.get('AZURE_STORAGE_CONNECTION_STRING')
        if azure_connection:
            try:
                self.backup_manager = AzureBackupManager(azure_connection)
                self.backup_scheduler = BackupScheduler(self.backup_manager)
                
                # Start automated backups in production
                if app.config.get('ENV') == 'production':
                    self.backup_scheduler.start_scheduler()
                    logger.info("Automated backup scheduler started")
                
            except Exception as e:
                logger.error(f"Failed to initialize backup system: {e}")
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Add CLI commands
        self._register_cli_commands(app)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down safely...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.backup_scheduler:
            self.backup_scheduler.stop_scheduler()
    
    def run_startup_checks(self):
        """Run post-deployment integrity checks on app startup"""
        try:
            logger.info("Running startup integrity checks...")
            
            # Run post-deployment check
            report = self.integrity_monitor.run_post_deployment_check()
            
            if report.overall_result.value == "FAIL":
                logger.critical("CRITICAL: Data integrity check failed on startup!")
                logger.critical("Recommendations:")
                for rec in report.recommendations:
                    logger.critical(f"  - {rec}")
                
                # In production, you might want to prevent app startup
                if self.app.config.get('ENV') == 'production':
                    logger.critical("Preventing application startup due to data integrity failure")
                    sys.exit(1)
            
            elif report.overall_result.value == "WARNING":
                logger.warning("Data integrity warnings detected on startup")
                for rec in report.recommendations:
                    logger.warning(f"  - {rec}")
            
            else:
                logger.info("✅ Data integrity check passed on startup")
            
            return report
            
        except Exception as e:
            logger.error(f"Startup integrity check failed: {e}")
            return None
    
    def create_pre_deployment_backup(self):
        """Create backup before deployment"""
        if not self.backup_manager:
            logger.warning("Backup manager not available - skipping pre-deployment backup")
            return False
        
        try:
            logger.info("Creating pre-deployment backup...")
            metadata = self.backup_manager.create_backup("pre_deployment")
            
            if metadata:
                logger.info(f"✅ Pre-deployment backup created: {metadata.backup_id}")
                return True
            else:
                logger.error("❌ Pre-deployment backup failed")
                return False
                
        except Exception as e:
            logger.error(f"Pre-deployment backup error: {e}")
            return False
    
    def get_system_health(self):
        """Get overall system health status"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check backup system health
            if self.backup_manager:
                backup_health = self.backup_manager.get_backup_health_status()
                health['backup_system'] = backup_health
                
                if backup_health['status'] == 'ERROR':
                    health['overall_status'] = 'ERROR'
                    health['issues'].append(f"Backup system error: {backup_health['message']}")
                elif backup_health['status'] == 'WARNING':
                    if health['overall_status'] == 'HEALTHY':
                        health['overall_status'] = 'WARNING'
                    health['warnings'].append(f"Backup system warning: {backup_health['message']}")
            else:
                health['warnings'].append("Backup system not configured")
            
            # Check database integrity
            try:
                if self.integrity_monitor.validate_acid_compliance():
                    health['database_integrity'] = 'PASS'
                else:
                    health['database_integrity'] = 'FAIL'
                    health['overall_status'] = 'ERROR'
                    health['issues'].append("Database ACID compliance test failed")
            except Exception as e:
                health['database_integrity'] = 'ERROR'
                health['overall_status'] = 'ERROR'
                health['issues'].append(f"Database integrity check error: {e}")
            
        except Exception as e:
            health['overall_status'] = 'ERROR'
            health['issues'].append(f"Health check error: {e}")
        
        return health
    
    def _register_cli_commands(self, app):
        """Register CLI commands for deployment safety"""
        
        @app.cli.command('pre-deploy-check')
        def pre_deploy_check_command():
            """Run pre-deployment checks and create backup"""
            print("=== PRE-DEPLOYMENT SAFETY CHECK ===")
            
            # Create pre-deployment backup
            if self.create_pre_deployment_backup():
                print("✅ Pre-deployment backup created")
            else:
                print("❌ Pre-deployment backup failed")
                sys.exit(1)
            
            # Save integrity snapshot
            if run_pre_deployment_check():
                print("✅ Pre-deployment integrity snapshot saved")
            else:
                print("❌ Pre-deployment integrity check failed")
                sys.exit(1)
            
            print("=== PRE-DEPLOYMENT CHECK COMPLETE ===")
        
        @app.cli.command('post-deploy-check')
        def post_deploy_check_command():
            """Run post-deployment integrity validation"""
            print("=== POST-DEPLOYMENT SAFETY CHECK ===")
            
            success = run_post_deployment_check()
            
            if success:
                print("✅ Post-deployment check passed")
            else:
                print("❌ Post-deployment check failed")
                sys.exit(1)
        
        @app.cli.command('backup-now')
        def backup_now_command():
            """Create manual backup"""
            if not self.backup_manager:
                print("❌ Backup system not configured")
                sys.exit(1)
            
            print("Creating manual backup...")
            metadata = self.backup_manager.create_backup("manual")
            
            if metadata:
                print(f"✅ Backup created: {metadata.backup_id}")
            else:
                print("❌ Backup failed")
                sys.exit(1)
        
        @app.cli.command('list-backups')
        def list_backups_command():
            """List available restore points"""
            if not self.backup_manager:
                print("❌ Backup system not configured")
                sys.exit(1)
            
            restore_points = self.backup_manager.list_restore_points()
            
            if not restore_points:
                print("No backups available")
                return
            
            print(f"{'Backup ID':<30} {'Timestamp':<20} {'Size (MB)':<10} {'Type'}")
            print("-" * 80)
            
            for point in restore_points:
                print(f"{point.backup_id:<30} {point.timestamp.strftime('%Y-%m-%d %H:%M'):<20} {point.size_mb:<10.1f} {point.description}")
        
        @app.cli.command('system-health')
        def system_health_command():
            """Check system health status"""
            health = self.get_system_health()
            
            print(f"=== SYSTEM HEALTH REPORT ===")
            print(f"Overall Status: {health['overall_status']}")
            print(f"Timestamp: {health['timestamp']}")
            
            if health.get('backup_system'):
                backup = health['backup_system']
                print(f"\nBackup System: {backup['status']}")
                print(f"  Last Backup: {backup.get('last_backup_time', 'Unknown')}")
                print(f"  Total Backups: {backup.get('total_backups', 0)}")
            
            print(f"Database Integrity: {health.get('database_integrity', 'Unknown')}")
            
            if health['issues']:
                print(f"\n🚨 ISSUES:")
                for issue in health['issues']:
                    print(f"  - {issue}")
            
            if health['warnings']:
                print(f"\n⚠️  WARNINGS:")
                for warning in health['warnings']:
                    print(f"  - {warning}")
            
            if health['overall_status'] != 'HEALTHY':
                sys.exit(1)

# Global instance
deployment_safety = DeploymentSafetyManager()

def init_deployment_safety(app):
    """Initialize deployment safety for Flask app"""
    deployment_safety.init_app(app)
    
    # Run startup checks
    deployment_safety.run_startup_checks()
    
    return deployment_safety
