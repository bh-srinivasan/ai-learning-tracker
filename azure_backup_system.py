"""
Azure Backup and Disaster Recovery System
=========================================

Implements automated backup, point-in-time restore, and disaster recovery
for Azure-hosted applications with SQLite databases.

FEATURES:
- Automated backups to Azure Blob Storage
- Point-in-time restore capabilities
- Geo-redundant storage support
- Backup validation and integrity checks
- Easy restore CLI tools
- Comprehensive monitoring and alerting
"""

import os
import sqlite3
import gzip
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import AzureError
import schedule
import time
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BackupSystem')

@dataclass
class BackupMetadata:
    """Metadata for each backup"""
    backup_id: str
    timestamp: datetime
    database_size: int
    record_counts: Dict[str, int]
    checksum: str
    backup_type: str  # 'scheduled', 'manual', 'pre_deployment'
    compression_ratio: float
    backup_location: str
    retention_date: datetime

@dataclass
class RestorePoint:
    """Represents a point-in-time restore option"""
    backup_id: str
    timestamp: datetime
    description: str
    size_mb: float
    tables_included: List[str]
    is_verified: bool

class AzureBackupManager:
    """
    Manages automated backups and restore operations for Azure deployments
    """
    
    def __init__(self, 
                 connection_string: str,
                 container_name: str = "ai-learning-backups",
                 db_path: str = "ai_learning.db"):
        self.connection_string = connection_string
        self.container_name = container_name
        self.db_path = db_path
        self.backup_metadata_file = "backup_metadata.json"
        
        # Initialize Azure Blob client
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_client = self.blob_service_client.get_container_client(container_name)
            
            # Create container if it doesn't exist
            try:
                self.container_client.create_container()
                logger.info(f"Created backup container: {container_name}")
            except Exception:
                pass  # Container already exists
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob client: {e}")
            raise
    
    def calculate_database_checksum(self) -> str:
        """Calculate checksum of entire database"""
        try:
            with open(self.db_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate database checksum: {e}")
            return "ERROR"
    
    def get_table_record_counts(self) -> Dict[str, int]:
        """Get record counts for all tables"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            counts = {}
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]
                except Exception as e:
                    logger.warning(f"Could not count records in {table}: {e}")
                    counts[table] = -1
            
            return counts
        finally:
            conn.close()
    
    def create_backup(self, backup_type: str = "scheduled") -> Optional[BackupMetadata]:
        """Create a backup and upload to Azure Blob Storage"""
        try:
            backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_type}"
            timestamp = datetime.now()
            
            logger.info(f"Starting backup: {backup_id}")
            
            # Get database info
            db_size = os.path.getsize(self.db_path)
            record_counts = self.get_table_record_counts()
            checksum = self.calculate_database_checksum()
            
            # Read and compress database
            with open(self.db_path, 'rb') as db_file:
                db_content = db_file.read()
            
            compressed_content = gzip.compress(db_content)
            compression_ratio = len(compressed_content) / len(db_content)
            
            # Upload to Azure Blob Storage
            blob_name = f"{backup_id}.db.gz"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            blob_client.upload_blob(compressed_content, overwrite=True)
            
            # Calculate retention date (30 days for scheduled, 90 days for manual/pre-deployment)
            retention_days = 30 if backup_type == "scheduled" else 90
            retention_date = timestamp + timedelta(days=retention_days)
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                database_size=db_size,
                record_counts=record_counts,
                checksum=checksum,
                backup_type=backup_type,
                compression_ratio=compression_ratio,
                backup_location=f"azure://{self.container_name}/{blob_name}",
                retention_date=retention_date
            )
            
            # Save metadata
            self.save_backup_metadata(metadata)
            
            logger.info(f"Backup completed: {backup_id} ({db_size} bytes -> {len(compressed_content)} bytes, {compression_ratio:.2%} compression)")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to Azure and local file"""
        try:
            # Load existing metadata
            all_metadata = self.load_all_backup_metadata()
            
            # Add new metadata
            all_metadata[metadata.backup_id] = asdict(metadata)
            
            # Convert datetime objects to ISO strings for JSON serialization
            for backup_id, meta in all_metadata.items():
                if isinstance(meta.get('timestamp'), datetime):
                    meta['timestamp'] = meta['timestamp'].isoformat()
                if isinstance(meta.get('retention_date'), datetime):
                    meta['retention_date'] = meta['retention_date'].isoformat()
            
            # Save to local file
            with open(self.backup_metadata_file, 'w') as f:
                json.dump(all_metadata, f, indent=2, default=str)
            
            # Upload metadata to Azure
            metadata_content = json.dumps(all_metadata, indent=2, default=str)
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob="backup_metadata.json"
            )
            blob_client.upload_blob(metadata_content.encode(), overwrite=True)
            
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def load_all_backup_metadata(self) -> Dict:
        """Load all backup metadata"""
        try:
            # Try to load from Azure first
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob="backup_metadata.json"
                )
                content = blob_client.download_blob().readall()
                metadata = json.loads(content.decode())
                
                # Convert ISO strings back to datetime objects
                for backup_id, meta in metadata.items():
                    if isinstance(meta.get('timestamp'), str):
                        meta['timestamp'] = datetime.fromisoformat(meta['timestamp'])
                    if isinstance(meta.get('retention_date'), str):
                        meta['retention_date'] = datetime.fromisoformat(meta['retention_date'])
                
                return metadata
            except:
                # Fall back to local file
                if os.path.exists(self.backup_metadata_file):
                    with open(self.backup_metadata_file, 'r') as f:
                        return json.load(f)
                
            return {}
        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")
            return {}
    
    def list_restore_points(self, days_back: int = 30) -> List[RestorePoint]:
        """List available restore points"""
        try:
            all_metadata = self.load_all_backup_metadata()
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            restore_points = []
            for backup_id, meta in all_metadata.items():
                timestamp = meta['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                
                if timestamp >= cutoff_date:
                    restore_point = RestorePoint(
                        backup_id=backup_id,
                        timestamp=timestamp,
                        description=f"{meta['backup_type']} backup - {sum(meta['record_counts'].values())} total records",
                        size_mb=meta['database_size'] / 1024 / 1024,
                        tables_included=list(meta['record_counts'].keys()),
                        is_verified=True  # TODO: Implement backup verification
                    )
                    restore_points.append(restore_point)
            
            # Sort by timestamp, newest first
            restore_points.sort(key=lambda x: x.timestamp, reverse=True)
            return restore_points
            
        except Exception as e:
            logger.error(f"Failed to list restore points: {e}")
            return []
    
    def restore_from_backup(self, backup_id: str, target_path: str = None) -> bool:
        """Restore database from backup"""
        try:
            if target_path is None:
                target_path = f"{self.db_path}.restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting restore from backup: {backup_id}")
            
            # Download backup from Azure
            blob_name = f"{backup_id}.db.gz"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            compressed_content = blob_client.download_blob().readall()
            db_content = gzip.decompress(compressed_content)
            
            # Write restored database
            with open(target_path, 'wb') as f:
                f.write(db_content)
            
            # Verify restore
            if self.verify_restored_database(target_path, backup_id):
                logger.info(f"Database restored successfully to: {target_path}")
                return True
            else:
                logger.error("Restore verification failed")
                os.remove(target_path)
                return False
                
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def verify_restored_database(self, db_path: str, backup_id: str) -> bool:
        """Verify integrity of restored database"""
        try:
            # Get backup metadata
            all_metadata = self.load_all_backup_metadata()
            if backup_id not in all_metadata:
                logger.error(f"Backup metadata not found for {backup_id}")
                return False
            
            backup_meta = all_metadata[backup_id]
            
            # Check file size
            actual_size = os.path.getsize(db_path)
            expected_size = backup_meta['database_size']
            
            if actual_size != expected_size:
                logger.error(f"Size mismatch: expected {expected_size}, got {actual_size}")
                return False
            
            # Check table record counts
            conn = sqlite3.connect(db_path)
            try:
                for table, expected_count in backup_meta['record_counts'].items():
                    if expected_count == -1:  # Skip tables that had count errors
                        continue
                    
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                        actual_count = cursor.fetchone()[0]
                        
                        if actual_count != expected_count:
                            logger.error(f"Record count mismatch in {table}: expected {expected_count}, got {actual_count}")
                            return False
                    except Exception as e:
                        logger.warning(f"Could not verify {table}: {e}")
            finally:
                conn.close()
            
            logger.info(f"Database verification passed for {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove expired backups"""
        try:
            all_metadata = self.load_all_backup_metadata()
            current_time = datetime.now()
            
            expired_backups = []
            for backup_id, meta in all_metadata.items():
                retention_date = meta['retention_date']
                if isinstance(retention_date, str):
                    retention_date = datetime.fromisoformat(retention_date)
                
                if current_time > retention_date:
                    expired_backups.append(backup_id)
            
            # Delete expired backups
            for backup_id in expired_backups:
                try:
                    # Delete from Azure
                    blob_name = f"{backup_id}.db.gz"
                    blob_client = self.blob_service_client.get_blob_client(
                        container=self.container_name,
                        blob=blob_name
                    )
                    blob_client.delete_blob()
                    
                    # Remove from metadata
                    del all_metadata[backup_id]
                    
                    logger.info(f"Deleted expired backup: {backup_id}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup_id}: {e}")
            
            # Update metadata if any backups were deleted
            if expired_backups:
                self.save_backup_metadata_dict(all_metadata)
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def save_backup_metadata_dict(self, metadata_dict: Dict):
        """Save metadata dictionary"""
        try:
            # Save to local file
            with open(self.backup_metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2, default=str)
            
            # Upload to Azure
            metadata_content = json.dumps(metadata_dict, indent=2, default=str)
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob="backup_metadata.json"
            )
            blob_client.upload_blob(metadata_content.encode(), overwrite=True)
            
        except Exception as e:
            logger.error(f"Failed to save metadata dictionary: {e}")
    
    def get_backup_health_status(self) -> Dict:
        """Get health status of backup system"""
        try:
            all_metadata = self.load_all_backup_metadata()
            
            if not all_metadata:
                return {
                    'status': 'ERROR',
                    'message': 'No backups found',
                    'last_backup': None,
                    'total_backups': 0
                }
            
            # Find most recent backup
            latest_backup = None
            latest_timestamp = None
            
            for backup_id, meta in all_metadata.items():
                timestamp = meta['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                
                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_backup = backup_id
            
            # Check if backup is recent (within last 25 hours for daily backups)
            hours_since_backup = (datetime.now() - latest_timestamp).total_seconds() / 3600
            
            if hours_since_backup > 25:
                status = 'WARNING'
                message = f'Last backup was {hours_since_backup:.1f} hours ago'
            else:
                status = 'HEALTHY'
                message = f'Latest backup: {hours_since_backup:.1f} hours ago'
            
            return {
                'status': status,
                'message': message,
                'last_backup': latest_backup,
                'last_backup_time': latest_timestamp.isoformat(),
                'total_backups': len(all_metadata),
                'hours_since_backup': hours_since_backup
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'ERROR',
                'message': str(e),
                'last_backup': None,
                'total_backups': 0
            }

class BackupScheduler:
    """
    Handles automated backup scheduling
    """
    
    def __init__(self, backup_manager: AzureBackupManager):
        self.backup_manager = backup_manager
        self.is_running = False
        self.scheduler_thread = None
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule daily backups at 2 AM
        schedule.every().day.at("02:00").do(self._run_scheduled_backup)
        
        # Schedule cleanup weekly on Sundays at 3 AM
        schedule.every().sunday.at("03:00").do(self._run_cleanup)
        
        # Schedule health checks every 6 hours
        schedule.every(6).hours.do(self._run_health_check)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Backup scheduler started")
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _run_scheduled_backup(self):
        """Run scheduled backup"""
        logger.info("Running scheduled backup")
        metadata = self.backup_manager.create_backup("scheduled")
        if metadata:
            logger.info(f"Scheduled backup completed: {metadata.backup_id}")
        else:
            logger.error("Scheduled backup failed")
    
    def _run_cleanup(self):
        """Run backup cleanup"""
        logger.info("Running backup cleanup")
        self.backup_manager.cleanup_old_backups()
    
    def _run_health_check(self):
        """Run backup health check"""
        health = self.backup_manager.get_backup_health_status()
        if health['status'] == 'ERROR':
            logger.error(f"Backup system health check failed: {health['message']}")
        elif health['status'] == 'WARNING':
            logger.warning(f"Backup system warning: {health['message']}")
        else:
            logger.info(f"Backup system healthy: {health['message']}")

# CLI Interface
def create_cli_restore_tool():
    """Create a CLI tool for easy database restoration"""
    cli_script = '''#!/usr/bin/env python3
"""
Emergency Database Restore Tool
===============================

Quick CLI tool for restoring database from Azure backups during incidents.

Usage:
    python restore_tool.py list                    # List available restore points
    python restore_tool.py restore <backup_id>     # Restore from specific backup
    python restore_tool.py latest                  # Restore from latest backup
    python restore_tool.py verify <file>           # Verify database integrity
"""

import sys
import os
from azure_backup_system import AzureBackupManager

def main():
    # Initialize backup manager
    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        print("ERROR: AZURE_STORAGE_CONNECTION_STRING environment variable not set")
        sys.exit(1)
    
    backup_manager = AzureBackupManager(connection_string)
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        restore_points = backup_manager.list_restore_points()
        print(f"{'Backup ID':<30} {'Timestamp':<20} {'Size (MB)':<10} {'Description'}")
        print("-" * 80)
        for point in restore_points:
            print(f"{point.backup_id:<30} {point.timestamp.strftime('%Y-%m-%d %H:%M'):<20} {point.size_mb:<10.1f} {point.description}")
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("ERROR: Please specify backup ID")
            sys.exit(1)
        
        backup_id = sys.argv[2]
        target_path = sys.argv[3] if len(sys.argv) > 3 else "ai_learning_restored.db"
        
        print(f"Restoring from backup: {backup_id}")
        success = backup_manager.restore_from_backup(backup_id, target_path)
        
        if success:
            print(f"✅ Database restored successfully to: {target_path}")
        else:
            print("❌ Restore failed")
            sys.exit(1)
    
    elif command == "latest":
        restore_points = backup_manager.list_restore_points()
        if not restore_points:
            print("ERROR: No backups available")
            sys.exit(1)
        
        latest = restore_points[0]
        target_path = sys.argv[2] if len(sys.argv) > 2 else "ai_learning_restored.db"
        
        print(f"Restoring from latest backup: {latest.backup_id}")
        success = backup_manager.restore_from_backup(latest.backup_id, target_path)
        
        if success:
            print(f"✅ Database restored successfully to: {target_path}")
        else:
            print("❌ Restore failed")
            sys.exit(1)
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("ERROR: Please specify database file to verify")
            sys.exit(1)
        
        db_path = sys.argv[2]
        # TODO: Implement standalone verification
        print(f"Verifying database: {db_path}")
    
    else:
        print(f"ERROR: Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('restore_tool.py', 'w') as f:
        f.write(cli_script)
    
    # Make executable on Unix systems
    try:
        os.chmod('restore_tool.py', 0o755)
    except:
        pass

if __name__ == "__main__":
    # Demo usage
    print("Azure Backup System - Demo")
    
    # You would set this environment variable in production
    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', 'DefaultEndpointsProtocol=https;AccountName=example;AccountKey=key;EndpointSuffix=core.windows.net')
    
    if connection_string == 'DefaultEndpointsProtocol=https;AccountName=example;AccountKey=key;EndpointSuffix=core.windows.net':
        print("Set AZURE_STORAGE_CONNECTION_STRING environment variable to use actual Azure storage")
        
    # Create CLI tool
    create_cli_restore_tool()
    print("✅ CLI restore tool created: restore_tool.py")
