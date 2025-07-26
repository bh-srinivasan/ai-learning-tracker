"""
🚨 EMERGENCY AZURE DATA RECOVERY SCRIPT
=====================================

CRITICAL SITUATION: Azure database has 0 users and 0 courses
LOCAL STATUS: Local database has data intact
ACTION: Upload local database to restore Azure data immediately
"""

import sqlite3
import os
import sys
from datetime import datetime

def emergency_azure_recovery():
    """Emergency recovery: Push local database to Azure immediately"""
    
    print("🚨 EMERGENCY AZURE DATA RECOVERY")
    print("=" * 50)
    
    # Check local database first
    if not os.path.exists('ai_learning.db'):
        print("❌ CRITICAL: Local database ai_learning.db not found!")
        return False
    
    print(f"✅ Local database found: {os.path.getsize('ai_learning.db')} bytes")
    
    # Verify local data
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        users_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        courses_count = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
        
        print(f"📊 LOCAL DATA VERIFICATION:")
        print(f"   Users: {users_count}")
        print(f"   Courses: {courses_count}")
        
        if users_count == 0 and courses_count == 0:
            print("❌ CRITICAL: Local database is also empty!")
            conn.close()
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking local database: {e}")
        return False
    
    # Try Azure upload using azure_database_sync
    print("\n🔄 ATTEMPTING AZURE RECOVERY...")
    
    try:
        # Import the restored azure sync module
        from azure_database_sync import azure_db_sync
        
        print("✅ Azure sync module loaded")
        
        # Force upload to Azure
        success = azure_db_sync.upload_database_to_azure()
        
        if success:
            print("✅ SUCCESS: Local database uploaded to Azure!")
            print("🎉 Azure data recovery completed")
            return True
        else:
            print("❌ Failed to upload database to Azure")
            print("💡 Check Azure Storage configuration")
            return False
            
    except ImportError as e:
        print(f"❌ Azure sync module not available: {e}")
        print("💡 Azure Storage may not be configured")
        return False
    except Exception as e:
        print(f"❌ Error during Azure upload: {e}")
        return False

def backup_local_database():
    """Create a backup of local database before any operations"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ai_learning_backup_{timestamp}.db"
    
    try:
        import shutil
        shutil.copy2('ai_learning.db', backup_name)
        print(f"📦 Local database backed up to: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"⚠️ Warning: Could not create backup: {e}")
        return None

def manual_azure_restoration_guide():
    """Provide manual steps if automated recovery fails"""
    print("\n📋 MANUAL AZURE RECOVERY STEPS:")
    print("=" * 40)
    print("1. Check Azure App Service configuration:")
    print("   az webapp config show --resource-group ai-learning-rg --name ai-learning-tracker")
    print("\n2. Check Azure Storage connection:")
    print("   az webapp config appsettings list --resource-group ai-learning-rg --name ai-learning-tracker")
    print("\n3. Restart Azure App Service:")
    print("   az webapp restart --resource-group ai-learning-rg --name ai-learning-tracker")
    print("\n4. Monitor Azure logs:")
    print("   az webapp log tail --resource-group ai-learning-rg --name ai-learning-tracker")
    print("\n5. If all else fails, redeploy with data:")
    print("   git push azure master --force")

if __name__ == "__main__":
    print("🚨 AZURE DATA LOSS EMERGENCY RECOVERY")
    print("====================================")
    print("ISSUE: Azure database shows 0 users, 0 courses")
    print("ACTION: Attempting to restore from local database")
    print("")
    
    # Step 1: Backup local database
    backup_file = backup_local_database()
    
    # Step 2: Attempt automated recovery
    success = emergency_azure_recovery()
    
    if success:
        print("\n🎉 RECOVERY SUCCESSFUL!")
        print("✅ Azure database should now have your data restored")
        print("🔍 Please verify by checking the Azure application")
    else:
        print("\n❌ AUTOMATED RECOVERY FAILED")
        print("📋 Manual intervention required")
        manual_azure_restoration_guide()
    
    print(f"\n📦 Local backup created: {backup_file if backup_file else 'None'}")
    print("🔒 Your local data is safe and unchanged")
