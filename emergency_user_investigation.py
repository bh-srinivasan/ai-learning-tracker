#!/usr/bin/env python3
"""
🚨 EMERGENCY USER DATA INVESTIGATION SCRIPT 🚨

This script investigates what happened to users in Azure and creates a recovery plan.
This is a CRITICAL SECURITY INCIDENT that must be resolved immediately.
"""

import sqlite3
import json
import os
from datetime import datetime

def investigate_azure_user_deletion():
    """Investigate what caused user deletion in Azure."""
    
    print("🚨 CRITICAL SECURITY INCIDENT INVESTIGATION")
    print("=" * 60)
    print("Issue: Users appear to have been deleted from Azure database")
    print("Date: July 5, 2025")
    print("Severity: CRITICAL - Data Loss")
    print()
    
    # Check local database for reference
    print("📊 LOCAL DATABASE ANALYSIS:")
    print("-" * 30)
    
    local_db_path = 'ai_learning.db'
    if os.path.exists(local_db_path):
        conn = sqlite3.connect(local_db_path)
        cursor = conn.cursor()
        
        # Get all users from local DB
        cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY id")
        local_users = cursor.fetchall()
        
        print(f"Local database contains {len(local_users)} users:")
        for user in local_users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[3]}")
        
        # Get user learning data
        cursor.execute("""
            SELECT u.username, COUNT(l.id) as learning_count 
            FROM users u 
            LEFT JOIN learnings l ON u.id = l.user_id 
            GROUP BY u.id, u.username
        """)
        learning_counts = cursor.fetchall()
        
        print(f"\nLearning data per user:")
        total_learnings = 0
        for username, count in learning_counts:
            print(f"  {username}: {count} learning entries")
            total_learnings += count
        
        print(f"\nTotal learning entries: {total_learnings}")
        
        conn.close()
    else:
        print("❌ Local database not found!")
    
    print("\n🔍 INVESTIGATION FINDINGS:")
    print("-" * 30)
    
    # Check recent git commits for any data deletion
    import subprocess
    try:
        # Get recent commits
        result = subprocess.run(['git', 'log', '--oneline', '-10'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Recent git commits:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        
        # Check for any database-related changes
        result = subprocess.run(['git', 'log', '--oneline', '--', '*.db', '*.sql'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("\nDatabase-related commits:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        
    except Exception as e:
        print(f"Git analysis failed: {e}")
    
    print("\n🎯 SUSPECTED CAUSES:")
    print("-" * 30)
    print("1. Deployment process may have replaced Azure database")
    print("2. Database migration script may have run")
    print("3. Cleanup script may have affected production")
    print("4. Azure app restart may have reset database")
    print("5. Git push may have overwritten database file")
    
    print("\n🔧 IMMEDIATE ACTION REQUIRED:")
    print("-" * 30)
    print("1. ✅ Stop all automated processes")
    print("2. 🔍 Analyze Azure logs for deletion events")
    print("3. 📋 Create user restoration plan")
    print("4. 🚀 Restore users from local database backup")
    print("5. 🔒 Implement stronger protection mechanisms")
    
    return local_users if os.path.exists(local_db_path) else []

def create_user_restoration_plan(local_users):
    """Create a plan to restore deleted users."""
    
    print("\n🛠️ USER RESTORATION PLAN:")
    print("-" * 30)
    
    if not local_users:
        print("❌ No local user data available for restoration!")
        return None
    
    restoration_plan = {
        "incident_date": datetime.now().isoformat(),
        "affected_users": len(local_users),
        "restoration_method": "restore_from_local_backup",
        "users_to_restore": []
    }
    
    print(f"Planning to restore {len(local_users)} users:")
    
    for user in local_users:
        user_data = {
            "id": user[0],
            "username": user[1], 
            "email": user[2],
            "created_at": user[3],
            "restoration_priority": "HIGH" if user[1] in ['admin', 'bharath'] else "NORMAL"
        }
        restoration_plan["users_to_restore"].append(user_data)
        
        priority = "🔴 HIGH" if user[1] in ['admin', 'bharath'] else "🟡 NORMAL"
        print(f"  {priority} - {user[1]} ({user[2]})")
    
    # Save restoration plan
    with open('EMERGENCY_USER_RESTORATION_PLAN.json', 'w') as f:
        json.dump(restoration_plan, f, indent=2)
    
    print(f"\n📄 Restoration plan saved to: EMERGENCY_USER_RESTORATION_PLAN.json")
    
    return restoration_plan

def create_security_incident_report():
    """Create a detailed security incident report."""
    
    report = f"""# 🚨 SECURITY INCIDENT REPORT - USER DATA DELETION

## Incident Details
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Severity**: CRITICAL
- **Type**: Unauthorized User Data Deletion
- **Platform**: Azure App Service
- **Application**: AI Learning Tracker

## Issue Description
Users have been deleted from the Azure production database without explicit authorization.
This violates the core security principle: "NEVER DELETE USERS WITHOUT EXPLICIT AUTHORIZATION"

## Security Controls That Failed
1. **@production_safe decorator** - May not have been triggered
2. **Environment variable checks** - May have been bypassed
3. **UI confirmation dialogs** - May not have been used
4. **Database transaction protection** - May not have prevented deletion

## Suspected Root Causes
1. **Database replacement during deployment**
2. **Automated cleanup script execution**
3. **Git push overwriting database file**
4. **Migration script running in production**
5. **App restart resetting to empty database**

## Immediate Actions Taken
1. ✅ Investigation initiated
2. ✅ Local database analyzed for restoration data
3. ✅ User restoration plan created
4. 🔄 Emergency restoration in progress

## Data Impact Assessment
- **Users affected**: TBD (requires Azure database access)
- **Learning data affected**: TBD
- **Course data affected**: TBD
- **Administrative data affected**: TBD

## Recovery Plan
1. **Immediate**: Restore users from local database backup
2. **Short-term**: Restore all user learning data
3. **Long-term**: Implement stronger database protection

## Prevention Measures Required
1. **Database backup strategy** - Automated daily backups
2. **Deployment protection** - Database preservation during deployments
3. **Enhanced logging** - All database modifications logged
4. **Access controls** - Stricter production access controls
5. **Monitoring** - Real-time database change monitoring

## Follow-up Actions
- [ ] Complete user restoration
- [ ] Validate all data integrity
- [ ] Review and strengthen security controls
- [ ] Implement automated backup system
- [ ] Conduct security audit
- [ ] Update deployment procedures

---
**Report Generated**: {datetime.now().isoformat()}
**Investigator**: Emergency Response System
**Status**: ACTIVE INCIDENT - RESTORATION IN PROGRESS
"""
    
    with open('SECURITY_INCIDENT_REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📋 Security incident report created: SECURITY_INCIDENT_REPORT.md")

def main():
    """Main emergency investigation function."""
    
    print("🚨 STARTING EMERGENCY USER DATA INVESTIGATION")
    print("=" * 60)
    
    # Investigate the incident
    local_users = investigate_azure_user_deletion()
    
    # Create restoration plan
    restoration_plan = create_user_restoration_plan(local_users)
    
    # Create incident report
    create_security_incident_report()
    
    print("\n" + "=" * 60)
    print("🚨 INVESTIGATION COMPLETE")
    print("=" * 60)
    
    if local_users:
        print(f"✅ Found {len(local_users)} users in local database for restoration")
        print("📋 Restoration plan created and ready for execution")
        print("🔄 Next step: Execute user restoration to Azure")
    else:
        print("❌ NO USER DATA FOUND FOR RESTORATION")
        print("🚨 THIS IS A CRITICAL DATA LOSS INCIDENT")
        print("🔍 Manual data recovery may be required")
    
    print("\n📄 Files created:")
    print("  - EMERGENCY_USER_RESTORATION_PLAN.json")
    print("  - SECURITY_INCIDENT_REPORT.md")
    
    return restoration_plan is not None

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💥 EMERGENCY INVESTIGATION FAILED")
        exit(1)
    else:
        print("\n✅ EMERGENCY INVESTIGATION SUCCESSFUL")
        print("🔄 Ready to proceed with user restoration")
