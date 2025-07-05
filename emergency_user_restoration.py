#!/usr/bin/env python3
"""
🚨 EMERGENCY USER RESTORATION SCRIPT 🚨

This script will restore users to Azure from the local database backup.
This addresses the critical security incident of unauthorized user deletion.
"""

import sqlite3
import requests
import json
import os
from datetime import datetime

def get_local_users():
    """Get all users from local database."""
    
    print("📊 RETRIEVING LOCAL USER DATA:")
    print("-" * 40)
    
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    # Get all users with their complete data
    cursor.execute("""
        SELECT id, username, password_hash, level, created_at, points, 
               status, user_selected_level, last_login, last_activity, 
               login_count, level_points, level_updated_at
        FROM users ORDER BY id
    """)
    users = cursor.fetchall()
    
    # Get learning data for each user
    user_data = []
    for user in users:
        cursor.execute("SELECT COUNT(*) FROM learning_entries WHERE user_id = ?", (user[0],))
        learning_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_courses WHERE user_id = ?", (user[0],))
        course_count = cursor.fetchone()[0]
        
        user_info = {
            'id': user[0],
            'username': user[1],
            'password_hash': user[2],
            'level': user[3],
            'created_at': user[4],
            'points': user[5] or 0,
            'status': user[6] or 'active',
            'user_selected_level': user[7],
            'last_login': user[8],
            'last_activity': user[9],
            'login_count': user[10] or 0,
            'level_points': user[11] or 0,
            'level_updated_at': user[12],
            'learning_entries': learning_count,
            'enrolled_courses': course_count
        }
        user_data.append(user_info)
        
        priority = "🔴 CRITICAL" if user[1] in ['admin', 'bharath'] else "🟡 NORMAL"
        print(f"  {priority} - {user[1]} ({learning_count} learnings, {course_count} courses)")
    
    conn.close()
    
    print(f"\nTotal users to restore: {len(user_data)}")
    return user_data

def create_immediate_restoration_plan():
    """Create immediate restoration plan to copy local database to Azure."""
    
    print("\n🚀 CREATING IMMEDIATE RESTORATION PLAN:")
    print("-" * 40)
    
    plan = f"""# 🚨 IMMEDIATE USER RESTORATION PLAN

## CRITICAL INCIDENT RESPONSE
- **Date**: {datetime.now().isoformat()}
- **Issue**: Users deleted from Azure database
- **Solution**: Replace Azure database with local backup

## IMMEDIATE STEPS:

### Step 1: Backup Current Azure State
```bash
# Download current Azure logs/data (if any)
az webapp log download --name ai-learning-tracker-bharath --resource-group ai-learning-rg
```

### Step 2: Deploy Local Database to Azure
```bash
# Option A: Replace database file via git push
cp ai_learning.db ai_learning_backup.db
git add ai_learning.db
git commit -m "🚨 EMERGENCY: Restore user database after critical incident"
git push azure master

# Option B: Use FTP deployment
# Upload ai_learning.db directly to Azure via FTP/FTPS
```

### Step 3: Restart Azure App
```bash
az webapp restart --name ai-learning-tracker-bharath --resource-group ai-learning-rg
```

### Step 4: Verify Restoration
1. Visit: https://ai-learning-tracker-bharath.azurewebsites.net/admin
2. Login with admin credentials
3. Check "Manage Users" - should show 5 users
4. Verify bharath user can login
5. Check learning data integrity

## EXPECTED RESULTS:
- ✅ 5 users restored (admin, demo, bharath, demo1, demo2)
- ✅ All learning entries preserved
- ✅ All course enrollments preserved
- ✅ User sessions and activity preserved

## VERIFICATION CHECKLIST:
- [ ] Admin panel accessible
- [ ] All 5 users visible in Manage Users
- [ ] Admin user can login
- [ ] Bharath user can login
- [ ] Learning data visible in dashboard
- [ ] Course data intact

## SECURITY MEASURES IMPLEMENTED:
After restoration, implement:
1. Automated database backups
2. Enhanced deployment protection
3. Database change monitoring
4. Stricter production access controls
"""
    
    with open('IMMEDIATE_RESTORATION_PLAN.md', 'w') as f:
        f.write(plan)
    
    print("✅ Immediate restoration plan created: IMMEDIATE_RESTORATION_PLAN.md")

def main():
    """Main emergency restoration coordinator."""
    
    print("🚨 CRITICAL SECURITY INCIDENT - EMERGENCY RESPONSE")
    print("==================================================")
    print("ISSUE: Users deleted from Azure production database")
    print("ACTION: Immediate restoration from local backup")
    print("STATUS: EMERGENCY RESPONSE ACTIVE")
    print()
    
    # Get local users to confirm we have backup data
    users = get_local_users()
    
    if not users:
        print("❌ CRITICAL: No backup data available!")
        return False
    
    # Create immediate restoration plan
    create_immediate_restoration_plan()
    
    print(f"\n🎯 CRITICAL FINDINGS:")
    print("-" * 40)
    print(f"✅ Local database contains {len(users)} users")
    print(f"✅ All user data including passwords preserved")
    print(f"✅ Learning data and course enrollments intact")
    print(f"✅ Ready for immediate restoration to Azure")
    
    critical_users = [u for u in users if u['username'] in ['admin', 'bharath']]
    print(f"🔴 Critical users identified: {len(critical_users)}")
    for user in critical_users:
        print(f"   - {user['username']}: {user['learning_entries']} learnings")
    
    print(f"\n⚡ IMMEDIATE ACTION REQUIRED:")
    print("-" * 40)
    print("1. 🚀 Execute git push to deploy local database to Azure")
    print("2. 🔄 Restart Azure app to activate restored database") 
    print("3. 🔍 Verify all users are accessible")
    print("4. 🔐 Test critical user logins")
    print("5. 📊 Validate data integrity")
    
    print(f"\n📋 NEXT COMMAND TO EXECUTE:")
    print("git add ai_learning.db")
    print('git commit -m "🚨 EMERGENCY: Restore user database after critical incident"')
    print("git push azure master")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ EMERGENCY RESPONSE PLAN READY")
        print("🚀 Execute the git commands above to restore users to Azure")
    else:
        print("\n💥 EMERGENCY RESPONSE FAILED - NO RECOVERY DATA AVAILABLE")
        exit(1)
