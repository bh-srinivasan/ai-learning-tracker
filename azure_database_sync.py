"""
Azure Storage Database Sync Module

This module handles synchronization of SQLite database with Azure Blob Storage
to ensure data persistence across Azure App Service deployments.
"""
import os
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient
import shutil

logger = logging.getLogger(__name__)

class AzureDatabaseSync:
    def __init__(self):
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'database-backup')
        self.blob_name = 'ai_learning.db'
        self.local_db_path = 'ai_learning.db'
        self.backup_db_path = 'ai_learning_backup.db'
        
        if not self.connection_string:
            logger.warning("⚠️ AZURE_STORAGE_CONNECTION_STRING not found - running without Azure sync")
            self.enabled = False
        else:
            self.enabled = True
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            logger.info("✅ Azure Storage sync initialized")
    
    def is_enabled(self):
        """Check if Azure Storage sync is enabled"""
        return self.enabled
    
    def download_database_from_azure(self):
        """Download database from Azure Blob Storage to local filesystem"""
        if not self.enabled:
            logger.info("🔄 Azure Storage sync disabled - skipping download")
            return False
            
        try:
            logger.info("⬇️ Downloading database from Azure Storage...")
            
            # Create container if it doesn't exist
            container_client = self.blob_service_client.get_container_client(self.container_name)
            try:
                container_client.create_container()
                logger.info(f"📁 Created container: {self.container_name}")
            except Exception:
                logger.info(f"📁 Container already exists: {self.container_name}")
            
            # Download blob to local file
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=self.blob_name
            )
            
            # Check if blob exists
            if not blob_client.exists():
                logger.info("📥 No existing database found in Azure Storage - will create new one")
                return False
            
            # Download database
            with open(self.local_db_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            blob_properties = blob_client.get_blob_properties()
            logger.info(f"✅ Database downloaded from Azure Storage")
            logger.info(f"   Size: {blob_properties.size} bytes")
            logger.info(f"   Last Modified: {blob_properties.last_modified}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error downloading database from Azure Storage: {e}")
            return False
    
    def upload_database_to_azure(self):
        """Upload local database to Azure Blob Storage"""
        if not self.enabled:
            logger.info("🔄 Azure Storage sync disabled - skipping upload")
            return False
            
        if not os.path.exists(self.local_db_path):
            logger.warning(f"⚠️ Local database not found: {self.local_db_path}")
            return False
            
        try:
            logger.info("⬆️ Uploading database to Azure Storage...")
            
            # Create backup before upload
            if os.path.exists(self.backup_db_path):
                os.remove(self.backup_db_path)
            shutil.copy2(self.local_db_path, self.backup_db_path)
            logger.info(f"💾 Created backup: {self.backup_db_path}")
            
            # Upload to blob storage
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=self.blob_name
            )
            
            with open(self.local_db_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            file_size = os.path.getsize(self.local_db_path)
            logger.info(f"✅ Database uploaded to Azure Storage")
            logger.info(f"   Size: {file_size} bytes")
            logger.info(f"   Timestamp: {datetime.now()}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error uploading database to Azure Storage: {e}")
            return False
    
    def sync_from_azure_on_startup(self):
        """Download database from Azure on application startup"""
        logger.info("🚀 STARTUP: Syncing database from Azure Storage...")
        
        if not self.enabled:
            logger.info("🔄 Azure Storage sync disabled - using local database only")
            return
        
        # Check if local database exists
        local_exists = os.path.exists(self.local_db_path)
        
        if local_exists:
            local_size = os.path.getsize(self.local_db_path)
            local_modified = datetime.fromtimestamp(os.path.getmtime(self.local_db_path))
            logger.info(f"📁 Local database exists: {local_size} bytes, modified {local_modified}")
        
        # Try to download from Azure
        azure_downloaded = self.download_database_from_azure()
        
        if azure_downloaded:
            logger.info("✅ STARTUP SYNC: Using database from Azure Storage")
        elif local_exists:
            logger.info("✅ STARTUP SYNC: Using existing local database")
        else:
            logger.info("📝 STARTUP SYNC: No database found - will create new one")
    
    def sync_to_azure_periodically(self):
        """Upload database to Azure (called periodically)"""
        if not self.enabled:
            return
            
        logger.info("🔄 PERIODIC SYNC: Backing up database to Azure Storage...")
        success = self.upload_database_to_azure()
        
        if success:
            logger.info("✅ PERIODIC SYNC: Database backed up successfully")
        else:
            logger.error("❌ PERIODIC SYNC: Backup failed")
    
    def emergency_restore_from_azure(self):
        """Emergency restore if local database is corrupted"""
        logger.warning("🚨 EMERGENCY RESTORE: Attempting to restore from Azure Storage...")
        
        if not self.enabled:
            logger.error("❌ EMERGENCY RESTORE: Azure Storage sync disabled")
            return False
        
        # Rename corrupted database
        if os.path.exists(self.local_db_path):
            corrupted_path = f"{self.local_db_path}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.local_db_path, corrupted_path)
            logger.info(f"📁 Moved corrupted database to: {corrupted_path}")
        
        # Download fresh copy from Azure
        success = self.download_database_from_azure()
        
        if success:
            logger.info("✅ EMERGENCY RESTORE: Database restored from Azure Storage")
            return True
        else:
            logger.error("❌ EMERGENCY RESTORE: Failed to restore from Azure Storage")
            return False

# Global instance
azure_db_sync = AzureDatabaseSync()
