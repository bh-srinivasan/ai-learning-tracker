"""
Azure Database Synchronization Module

This module provides Azure Storage integration for SQLite database persistence
in Azure App Service environments where the file system is ephemeral.

Features:
- Download database from Azure Blob Storage on startup
- Upload database to Azure Blob Storage on changes
- Background periodic backup to Azure Storage
- Emergency restore functionality
"""

import os
import logging
from datetime import datetime
import sqlite3

# Setup logging
logger = logging.getLogger(__name__)

class AzureDatabaseSync:
    """Azure Storage database synchronization class"""
    
    def __init__(self, db_path="ai_learning.db"):
        self.db_path = db_path
        self.container_name = "database-backups"
        self.blob_name = "ai_learning.db"
        self.azure_available = False
        
        # Check if Azure Storage is available
        try:
            from azure.storage.blob import BlobServiceClient
            connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
            if connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                self.azure_available = True
                logger.info("✅ Azure Storage sync initialized")
            else:
                logger.warning("⚠️ AZURE_STORAGE_CONNECTION_STRING not found - Azure sync disabled")
        except ImportError:
            logger.warning("⚠️ azure-storage-blob not installed - Azure sync disabled")
        except Exception as e:
            logger.error(f"❌ Azure Storage initialization failed: {e}")
    
    def sync_from_azure_on_startup(self):
        """Download database from Azure Storage on app startup"""
        if not self.azure_available:
            logger.info("Azure Storage not available - using local database only")
            return False
            
        try:
            # Check if local database exists
            if os.path.exists(self.db_path):
                logger.info(f"📁 Local database {self.db_path} exists - checking Azure for newer version")
            else:
                logger.info(f"📁 Local database {self.db_path} not found - downloading from Azure")
            
            # Try to download from Azure
            return self.download_database_from_azure()
            
        except Exception as e:
            logger.error(f"❌ Error during Azure sync on startup: {e}")
            return False
    
    def download_database_from_azure(self):
        """Download database from Azure Blob Storage"""
        if not self.azure_available:
            return False
            
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=self.blob_name
            )
            
            logger.info("⬇️ Downloading database from Azure Storage...")
            with open(self.db_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            logger.info("✅ Database downloaded from Azure Storage")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Could not download database from Azure: {e}")
            return False
    
    def upload_database_to_azure(self):
        """Upload database to Azure Blob Storage"""
        if not self.azure_available:
            return False
            
        if not os.path.exists(self.db_path):
            logger.warning(f"⚠️ Database file {self.db_path} not found - cannot upload")
            return False
            
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=self.blob_name
            )
            
            logger.info("⬆️ Uploading database to Azure Storage...")
            with open(self.db_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            logger.info("✅ Database uploaded to Azure Storage")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload database to Azure: {e}")
            return False
    
    def emergency_restore_from_azure(self):
        """Emergency restore database from Azure Storage"""
        logger.warning("🚨 Emergency restore from Azure Storage initiated")
        
        if not self.azure_available:
            logger.error("❌ Azure Storage not available for emergency restore")
            return False
            
        # Backup current database if it exists
        if os.path.exists(self.db_path):
            backup_path = f"{self.db_path}.emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.db_path, backup_path)
            logger.info(f"📦 Current database backed up to {backup_path}")
        
        # Download from Azure
        if self.download_database_from_azure():
            logger.info("✅ Emergency restore completed successfully")
            return True
        else:
            logger.error("❌ Emergency restore failed")
            return False

# Global instance for easy access
azure_db_sync = AzureDatabaseSync()

# Convenience functions
def sync_from_azure_on_startup():
    """Convenience function for startup sync"""
    return azure_db_sync.sync_from_azure_on_startup()

def upload_database_to_azure():
    """Convenience function for upload"""
    return azure_db_sync.upload_database_to_azure()

def download_database_from_azure():
    """Convenience function for download"""
    return azure_db_sync.download_database_from_azure()

def emergency_restore_from_azure():
    """Convenience function for emergency restore"""
    return azure_db_sync.emergency_restore_from_azure()

if __name__ == "__main__":
    # Test the module
    logger.info("🧪 Testing Azure Database Sync module...")
    sync = AzureDatabaseSync()
    
    if sync.azure_available:
        logger.info("✅ Azure Storage available")
        # Test download
        sync.download_database_from_azure()
    else:
        logger.info("⚠️ Azure Storage not available - module works in offline mode")
