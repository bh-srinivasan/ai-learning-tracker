# Data Protection CLI Commands
# ============================

## Pre-Deployment Commands
```bash
# Create backup and save integrity snapshot before deployment
flask pre-deploy-check

# Create manual backup
flask backup-now
```

## Post-Deployment Commands
```bash
# Verify data integrity after deployment
flask post-deploy-check

# Check system health
flask system-health
```

## Backup Management
```bash
# List available restore points
flask list-backups

# Create manual backup
flask backup-now
```

## Emergency Recovery
```bash
# Use the CLI restore tool for emergency recovery
python restore_tool.py list                    # List backups
python restore_tool.py restore <backup_id>     # Restore specific backup
python restore_tool.py latest                  # Restore from latest backup
```

## Automated Testing
```bash
# Test complete backup/restore cycle
python test_backup_system.py
```

## Azure Setup
```bash
# Set up Azure resources (run once)
./setup_azure_backup.sh
```

## Integration with Deployment Pipeline

### GitHub Actions
Add these secrets to your repository:
- AZURE_STORAGE_CONNECTION_STRING
- AZURE_WEBAPP_PUBLISH_PROFILE
- SLACK_WEBHOOK (optional, for notifications)

### Azure DevOps
Add these variables:
- AzureStorageConnectionString
- azureServiceConnection

## Monitoring and Alerts

The system provides:
- Automated daily backups
- Real-time data integrity monitoring
- Point-in-time restore capabilities
- Geo-redundant storage
- Automated cleanup of old backups
- Health monitoring and alerting

## Emergency Procedures

### Data Loss Detected
1. Stop application traffic
2. Run: `flask system-health`
3. Run: `python restore_tool.py latest`
4. Verify restored data
5. Investigate root cause

### Backup System Failure
1. Check Azure storage connectivity
2. Verify AZURE_STORAGE_CONNECTION_STRING
3. Run: `python test_backup_system.py`
4. Check Azure portal for storage account status
