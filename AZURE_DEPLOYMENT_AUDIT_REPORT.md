# Azure Deployment Security Audit Report
Generated: Unknown

## Executive Summary

❌ **DEPLOYMENT BLOCKED**: Critical user management issues found

## User Management Operations Audit

- **Files Audited**: 946
- **Dangerous Operations**: 44
- **Safe Operations**: 21

### ⚠️  Dangerous Operations Found

**File**: `app.py` (Line 2007)
**Pattern**: `DELETE\s+FROM\s+users`
**Match**: `DELETE FROM users`
```
    2004:         conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
    2005:         conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
    2006:         conn.execute('DELETE FROM user_personal_courses WHERE user_id = ?', (user_id,))
>>> 2007:         conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    2008:         conn.commit()
    2009:         
    2010:         # Log successful deletion
```

**File**: `app.py` (Line 2766)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
    2763:             
    2764:             for user in users:
    2765:                 conn.execute(
>>> 2766:                     'UPDATE users SET password_hash = ? WHERE id = ?',
    2767:                     (password_hash, user['id'])
    2768:                 )
    2769:                 updated_count += 1
```

**File**: `app.py` (Line 2858)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
    2855:         updated_count = 0
    2856:         for user in users:
    2857:             conn.execute(
>>> 2858:                 'UPDATE users SET password_hash = ? WHERE id = ?',
    2859:                 (password_hash, user['id'])
    2860:             )
    2861:             updated_count += 1
```

**File**: `app.py` (Line 2933)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
    2930:         
    2931:         # Update user's password
    2932:         conn.execute(
>>> 2933:             'UPDATE users SET password_hash = ? WHERE id = ?',
    2934:             (password_hash, user_id)
    2935:         )
    2936:         conn.commit()
```

**File**: `app.py` (Line 3020)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
    3017:                 # Hash and update the user's password
    3018:                 password_hash = generate_password_hash(temp_password)
    3019:                 conn.execute(
>>> 3020:                     'UPDATE users SET password_hash = ? WHERE id = ?',
    3021:                     (password_hash, user_id)
    3022:                 )
    3023:                 conn.commit()
```

**File**: `app.py` (Line 3043)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
    3040:                 temp_password = f"TempPass{secrets.randbelow(1000)}!"
    3041:                 password_hash = generate_password_hash(temp_password)
    3042:                 conn.execute(
>>> 3043:                     'UPDATE users SET password_hash = ? WHERE id = ?',
    3044:                     (password_hash, user_id)
    3045:                 )
    3046:                 conn.commit()
```

**File**: `app.py` (Line 3126)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
    3123:             
    3124:             # Update admin password
    3125:             result = conn.execute(
>>> 3126:                 'UPDATE users SET password_hash = ? WHERE username = ?',
    3127:                 (password_hash, 'admin')
    3128:             )
    3129:             conn.commit()
```

**File**: `app.py` (Line 2007)
**Pattern**: `conn\.execute.*DELETE.*users`
**Match**: `conn.execute('DELETE FROM users`
```
    2004:         conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
    2005:         conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
    2006:         conn.execute('DELETE FROM user_personal_courses WHERE user_id = ?', (user_id,))
>>> 2007:         conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    2008:         conn.commit()
    2009:         
    2010:         # Log successful deletion
```

**File**: `app.py` (Line 2886)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
    2883: @require_admin
    2884: @password_reset_guard(ui_triggered=True, require_explicit_request=False)
    2885: @production_safe('ui_triggered_password_reset')
>>> 2886: def admin_reset_user_password():
    2887:     """Reset password for individual user with custom password - Production safe"""
    2888:     user_id = request.form.get('user_id')
    2889:     custom_password = request.form.get('custom_password')
```

**File**: `app.py` (Line 1974)
**Pattern**: `delete_user\(`
**Match**: `delete_user(`
```
    1971: @app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
    1972: @require_admin
    1973: @security_guard('user_delete', require_ui=True)
>>> 1974: def admin_delete_user(user_id):
    1975:     """Delete a user (admin only) - Protected by security guards"""
    1976:     conn = get_db_connection()
    1977:     try:
```

**File**: `app.py` (Line 2726)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
    2723:         
    2724:         # Apply security guard validation for UI-triggered operation
    2725:         try:
>>> 2726:             SecurityGuard.validate_operation('bulk_password_reset', explicit_authorization=True)
    2727:             SecurityGuard.validate_azure_deployment_safety('bulk_password_reset', ui_triggered=True)
    2728:             SecurityGuard.require_ui_interaction()
    2729:         except SecurityGuardError as e:
```

**File**: `app.py` (Line 2727)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
    2724:         # Apply security guard validation for UI-triggered operation
    2725:         try:
    2726:             SecurityGuard.validate_operation('bulk_password_reset', explicit_authorization=True)
>>> 2727:             SecurityGuard.validate_azure_deployment_safety('bulk_password_reset', ui_triggered=True)
    2728:             SecurityGuard.require_ui_interaction()
    2729:         except SecurityGuardError as e:
    2730:             flash(f'Security Guard: {str(e)}', 'error')
```

**File**: `app.py` (Line 2731)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
    2728:             SecurityGuard.require_ui_interaction()
    2729:         except SecurityGuardError as e:
    2730:             flash(f'Security Guard: {str(e)}', 'error')
>>> 2731:             log_admin_action('bulk_password_reset_blocked', 'Attempted bulk password reset', 
    2732:                            session.get('user_id'), request.remote_addr)
    2733:             return render_template('admin/password_reset.html')
    2734:         
```

**File**: `azure_deployment_security_audit.py` (Line 43)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
      40:             r"reset_user_password\(",
      41:             r"delete_user\(",
      42:             r"remove_user\(",
>>>   43:             r"bulk_password_reset",
      44:             r"cleanup_database",
      45:         ]
      46:         
```

**File**: `azure_deployment_security_audit.py` (Line 44)
**Pattern**: `cleanup_database`
**Match**: `cleanup_database`
```
      41:             r"delete_user\(",
      42:             r"remove_user\(",
      43:             r"bulk_password_reset",
>>>   44:             r"cleanup_database",
      45:         ]
      46:         
      47:         # Safe operation patterns
```

**File**: `cleanup_database.py` (Line 70)
**Pattern**: `DELETE\s+FROM\s+users`
**Match**: `DELETE FROM users`
```
      67:             print(f"   - Removed {entries_removed} learning entries")
      68:             
      69:             # Remove user
>>>   70:             conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
      71:             user_removed = conn.execute('SELECT changes()').fetchone()[0]
      72:             
      73:             if user_removed > 0:
```

**File**: `cleanup_database.py` (Line 70)
**Pattern**: `conn\.execute.*DELETE.*users`
**Match**: `conn.execute('DELETE FROM users`
```
      67:             print(f"   - Removed {entries_removed} learning entries")
      68:             
      69:             # Remove user
>>>   70:             conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
      71:             user_removed = conn.execute('SELECT changes()').fetchone()[0]
      72:             
      73:             if user_removed > 0:
```

**File**: `cleanup_database.py` (Line 10)
**Pattern**: `cleanup_database`
**Match**: `cleanup_database`
```
       7: import sqlite3
       8: import sys
       9: 
>>>   10: def cleanup_database():
      11:     """Remove non-essential users from the database"""
      12:     print("🧹 AI Learning Tracker - Database Cleanup")
      13:     print("=" * 50)
```

**File**: `cleanup_database.py` (Line 127)
**Pattern**: `cleanup_database`
**Match**: `cleanup_database`
```
     124:         print(f"   ❌ Error verifying users: {str(e)}")
     125: 
     126: if __name__ == "__main__":
>>>  127:     success = cleanup_database()
     128:     if success:
     129:         verify_essential_users()
     130:         print("\n💡 Next steps:")
```

**File**: `fix_bharath_login.py` (Line 40)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
      37:         print("   Updating password to 'bharath'...")
      38:         
      39:         new_hash = generate_password_hash('bharath')
>>>   40:         conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
      41:                     (new_hash, 'bharath'))
      42:         conn.commit()
      43:         
```

**File**: `fix_bharath_login.py` (Line 40)
**Pattern**: `conn\.execute.*UPDATE.*password`
**Match**: `conn.execute('UPDATE users SET password`
```
      37:         print("   Updating password to 'bharath'...")
      38:         
      39:         new_hash = generate_password_hash('bharath')
>>>   40:         conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
      41:                     (new_hash, 'bharath'))
      42:         conn.commit()
      43:         
```

**File**: `fix_bharath_password.py` (Line 17)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
      14:     
      15:     # Update bharath's password
      16:     conn.execute(
>>>   17:         'UPDATE users SET password_hash = ? WHERE username = ?',
      18:         (bharath_hash, 'bharath')
      19:     )
      20:     conn.commit()
```

**File**: `investigate_db.py` (Line 200)
**Pattern**: `DELETE\s+FROM\s+users`
**Match**: `DELETE FROM users`
```
     197:         # Check for dangerous patterns
     198:         dangerous_patterns = [
     199:             'DROP TABLE',
>>>  200:             'DELETE FROM users',
     201:             'TRUNCATE',
     202:             'CREATE TABLE users',  # Without IF NOT EXISTS
     203:         ]
```

**File**: `password_monitor.py` (Line 158)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
     155:                 
     156:                 new_hash = generate_password_hash(BHARATH_TARGET_PASSWORD)
     157:                 conn.execute(
>>>  158:                     "UPDATE users SET password_hash = ? WHERE username = 'bharath'", 
     159:                     (new_hash,)
     160:                 )
     161:                 conn.commit()
```

**File**: `reset_admin_env_password.py` (Line 56)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users 
                SET password_hash`
```
      53:             # Update admin password
      54:             admin_hash = generate_password_hash(admin_password)
      55:             cursor.execute('''
>>>   56:                 UPDATE users 
      57:                 SET password_hash = ?, last_activity = CURRENT_TIMESTAMP 
      58:                 WHERE username = ?
      59:             ''', (admin_hash, 'admin'))
```

**File**: `reset_all_passwords.py` (Line 54)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users 
            SET password_hash`
```
      51:         # Update password
      52:         password_hash = generate_password_hash(password)
      53:         cursor.execute('''
>>>   54:             UPDATE users 
      55:             SET password_hash = ?, last_activity = CURRENT_TIMESTAMP 
      56:             WHERE username = ?
      57:         ''', (password_hash, username))
```

**File**: `reset_all_passwords.py` (Line 20)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
      17: )
      18: 
      19: @password_reset_guard(ui_triggered=False, require_explicit_request=True)
>>>   20: def reset_user_password(username, password, display_name, explicit_user_request=False):
      21:     """
      22:     Reset a user's password - requires explicit user authorization
      23:     
```

**File**: `reset_all_passwords.py` (Line 99)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
      96:     print("   By running this script, you are explicitly authorizing password resets")
      97:     
      98:     # Reset admin password (with explicit authorization)
>>>   99:     admin_success = reset_user_password('admin', admin_password, 'Admin', explicit_user_request=True)
     100:     
     101:     # Reset demo user password (with explicit authorization)
     102:     demo_success = reset_user_password('demo', demo_password, 'Demo User', explicit_user_request=True)
```

**File**: `reset_all_passwords.py` (Line 102)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
      99:     admin_success = reset_user_password('admin', admin_password, 'Admin', explicit_user_request=True)
     100:     
     101:     # Reset demo user password (with explicit authorization)
>>>  102:     demo_success = reset_user_password('demo', demo_password, 'Demo User', explicit_user_request=True)
     103:     
     104:     print("\n" + "=" * 55)
     105:     print("📊 Password Reset Results:")
```

**File**: `reset_bharath.py` (Line 17)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
      14:     
      15:     # Update bharath's password
      16:     conn.execute(
>>>   17:         'UPDATE users SET password_hash = ? WHERE username = ?',
      18:         (new_hash, 'bharath')
      19:     )
      20:     conn.commit()
```

**File**: `safe_password_reset.py` (Line 53)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users 
                SET password_hash`
```
      50:             # Update password
      51:             password_hash = generate_password_hash(password)
      52:             cursor.execute('''
>>>   53:                 UPDATE users 
      54:                 SET password_hash = ?, last_activity = CURRENT_TIMESTAMP 
      55:                 WHERE username = ?
      56:             ''', (password_hash, username))
```

**File**: `safe_password_reset.py` (Line 19)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
      16:     """Check if user is protected from password resets"""
      17:     return username in PROTECTED_USERS
      18: 
>>>   19: def reset_user_password(username, password, display_name, force=False):
      20:     """Reset a user's password with protection checks"""
      21:     
      22:     # Check if user is protected
```

**File**: `safe_password_reset.py` (Line 95)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
      92:     print("\n🔄 Resetting passwords...")
      93:     
      94:     # Reset admin password (primary admin)
>>>   95:     admin_success = reset_user_password('admin', admin_password, 'Admin')
      96:     
      97:     # Reset demo user password (for testing)
      98:     demo_success = reset_user_password(demo_username, demo_password, 'Demo')
```

**File**: `safe_password_reset.py` (Line 98)
**Pattern**: `reset_user_password\(`
**Match**: `reset_user_password(`
```
      95:     admin_success = reset_user_password('admin', admin_password, 'Admin')
      96:     
      97:     # Reset demo user password (for testing)
>>>   98:     demo_success = reset_user_password(demo_username, demo_password, 'Demo')
      99:     
     100:     # Show bharath status without modifying
     101:     print(f"\n🛡️  Protected user 'bharath' - password unchanged")
```

**File**: `security_guard.py` (Line 31)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
      28:     DANGEROUS_OPERATIONS = [
      29:         'password_reset',
      30:         'user_delete',
>>>   31:         'bulk_password_reset',
      32:         'user_suspend',
      33:         'database_cleanup',
      34:         'user_removal',
```

**File**: `security_guard.py` (Line 52)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
      49:     # Operations requiring UI interaction (frontend-triggered only)
      50:     UI_ONLY_OPERATIONS = [
      51:         'admin_password_reset',  # Admin password resets must come through UI
>>>   52:         'bulk_password_reset',   # Bulk resets must be UI-triggered
      53:         'individual_password_reset'  # Individual resets must be UI-triggered
      54:     ]
      55:     
```

**File**: `security_guard.py` (Line 209)
**Pattern**: `bulk_password_reset`
**Match**: `bulk_password_reset`
```
     206:             ui_only_in_production = [
     207:                 'password_reset',
     208:                 'user_delete',
>>>  209:                 'bulk_password_reset',
     210:                 'user_suspend',
     211:                 'database_cleanup'
     212:             ]
```

**File**: `update_azure_passwords.py` (Line 43)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
      40:         # Update admin password
      41:         cursor = conn.execute('SELECT username FROM users WHERE username = ?', ('admin',))
      42:         if cursor.fetchone():
>>>   43:             conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
      44:                         (admin_hash, 'admin'))
      45:             print("✅ Updated admin password")
      46:         else:
```

**File**: `update_azure_passwords.py` (Line 55)
**Pattern**: `UPDATE\s+users\s+SET\s+password_hash`
**Match**: `UPDATE users SET password_hash`
```
      52:         # Update demo password
      53:         cursor = conn.execute('SELECT username FROM users WHERE username = ?', (demo_username,))
      54:         if cursor.fetchone():
>>>   55:             conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
      56:                         (demo_hash, demo_username))
      57:             print(f"✅ Updated {demo_username} password")
      58:         else:
```

**File**: `update_azure_passwords.py` (Line 43)
**Pattern**: `conn\.execute.*UPDATE.*password`
**Match**: `conn.execute('UPDATE users SET password`
```
      40:         # Update admin password
      41:         cursor = conn.execute('SELECT username FROM users WHERE username = ?', ('admin',))
      42:         if cursor.fetchone():
>>>   43:             conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
      44:                         (admin_hash, 'admin'))
      45:             print("✅ Updated admin password")
      46:         else:
```

**File**: `update_azure_passwords.py` (Line 55)
**Pattern**: `conn\.execute.*UPDATE.*password`
**Match**: `conn.execute('UPDATE users SET password`
```
      52:         # Update demo password
      53:         cursor = conn.execute('SELECT username FROM users WHERE username = ?', (demo_username,))
      54:         if cursor.fetchone():
>>>   55:             conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
      56:                         (demo_hash, demo_username))
      57:             print(f"✅ Updated {demo_username} password")
      58:         else:
```

**File**: `admin\routes.py` (Line 366)
**Pattern**: `DELETE\s+FROM\s+users`
**Match**: `DELETE FROM users`
```
     363:         conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
     364:         
     365:         # Delete the user
>>>  366:         conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
     367:         conn.commit()
     368:         
     369:         flash(f'User {user["username"]} deleted successfully!', 'success')
```

**File**: `admin\routes.py` (Line 366)
**Pattern**: `conn\.execute.*DELETE.*users`
**Match**: `conn.execute('DELETE FROM users`
```
     363:         conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
     364:         
     365:         # Delete the user
>>>  366:         conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
     367:         conn.commit()
     368:         
     369:         flash(f'User {user["username"]} deleted successfully!', 'success')
```

**File**: `admin\routes.py` (Line 348)
**Pattern**: `delete_user\(`
**Match**: `delete_user(`
```
     345:     return redirect(url_for('admin.courses'))
     346: 
     347: @admin_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
>>>  348: def delete_user(user_id):
     349:     if not is_admin():
     350:         flash('Access denied. Admin privileges required.', 'error')
     351:         return redirect(url_for('dashboard.index'))
```

## Environment Safeguards

- **Environment Variable Detection**: ✅ PASS
  Environment variables are used for configuration
- **Security Guard Integration**: ✅ PASS
  Security guard system is imported and used
- **Production Environment Protection**: ✅ PASS
  Production environment protection implemented

## Hardcoded Credential Issues

🔴 **app.py** (Line 3009): `password = ''`
🔴 **app.py** (Line 312): `admin_password =`
🔴 **app.py** (Line 2713): `admin/password-reset', methods=`
🔴 **app.py** (Line 2793): `admin/validate-password', methods=`
🔴 **app.py** (Line 2812): `admin/reset-all-user-passwords', methods=`
🔴 **app.py** (Line 2882): `admin/reset-user-password', methods=`
🔴 **app.py** (Line 2955): `admin/view-user-password', methods=`
🔴 **app.py** (Line 2961): `admin_password =`
🔴 **app.py** (Line 3068): `admin/change-password', methods=`
🔴 **app.py** (Line 314): `demo_password =`
🔴 **app_clean.py** (Line 235): `admin_password =`
🔴 **app_clean.py** (Line 236): `demo_password =`
🔴 **app_simple.py** (Line 128): `admin_password =`
🔴 **app_simple.py** (Line 129): `demo_password =`
🔴 **azure_deployment_security_audit.py** (Line 190): `Password123`
🔴 **azure_deployment_security_audit.py** (Line 191): `admin.*password.*=`
🔴 **azure_deployment_security_audit.py** (Line 192): `demo.*password.*=`
🟡 **azure_deployment_security_audit.py** (Line 193): `bharath`
🟡 **azure_deployment_security_audit.py** (Line 179): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 180): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 182): `Hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 187): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 188): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 194): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 207): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 232): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 287): `Hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 300): `hardcoded`
🟡 **azure_deployment_security_audit.py** (Line 336): `hardcoded`
🔴 **azure_env_setup_instructions.py** (Line 30): `Password123`
🔴 **azure_env_setup_instructions.py** (Line 33): `Password123`
🟡 **azure_env_setup_instructions.py** (Line 20): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 31): `BHARATH`
🟡 **azure_env_setup_instructions.py** (Line 31): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 45): `BHARATH`
🟡 **azure_env_setup_instructions.py** (Line 46): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 54): `BHARATH`
🟡 **azure_env_setup_instructions.py** (Line 55): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 55): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 56): `BHARATH`
🟡 **azure_env_setup_instructions.py** (Line 58): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 71): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 95): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 95): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 111): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 112): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 113): `bharath`
🟡 **azure_env_setup_instructions.py** (Line 117): `BHARATH`
🟡 **azure_env_setup_instructions.py** (Line 111): `hardcoded`
🔴 **azure_status_summary.py** (Line 22): `Password123`
🟡 **azure_status_summary.py** (Line 67): `bharath`
🟡 **azure_status_summary.py** (Line 68): `bharath`
🟡 **azure_status_summary.py** (Line 69): `bharath`
🔴 **check_azure_status.py** (Line 67): `Password123`
🔴 **check_azure_status.py** (Line 69): `Password123`
🟡 **check_azure_status.py** (Line 12): `bharath`
🟡 **check_azure_status.py** (Line 60): `bharath`
🟡 **check_azure_status.py** (Line 89): `bharath`
🔴 **check_bharath_user.py** (Line 57): `ADMIN PASSWORD RESET EVENTS ===`
🟡 **check_bharath_user.py** (Line 3): `bharath`
🟡 **check_bharath_user.py** (Line 8): `bharath`
🟡 **check_bharath_user.py** (Line 19): `bharath`
🟡 **check_bharath_user.py** (Line 20): `BHARATH`
🟡 **check_bharath_user.py** (Line 21): `bharath`
🟡 **check_bharath_user.py** (Line 33): `Bharath`
🟡 **check_bharath_user.py** (Line 36): `bharath`
🟡 **check_bharath_user.py** (Line 37): `BHARATH`
🟡 **check_bharath_user.py** (Line 41): `bharath`
🟡 **check_bharath_user.py** (Line 54): `bharath`
🟡 **check_bharath_user.py** (Line 79): `bharath`
🟡 **check_bharath_user.py** (Line 82): `bharath`
🔴 **check_env_status.py** (Line 28): `Password123`
🔴 **check_env_status.py** (Line 30): `Password123`
🔴 **check_env_status.py** (Line 48): `Password123`
🟡 **check_env_status.py** (Line 53): `bharath`
🟡 **check_passwords.py** (Line 13): `bharath`
🟡 **check_passwords.py** (Line 23): `bharath`
🟡 **cleanup_database.py** (Line 45): `bharath`
🔴 **comprehensive_test.py** (Line 24): `admin_password =`
🔴 **comprehensive_test.py** (Line 25): `demo_password =`
🔴 **config.py** (Line 23): `ADMIN_PASSWORD =`
🔴 **config.py** (Line 68): `ADMIN_PASSWORD ==`
🔴 **config.py** (Line 25): `DEMO_PASSWORD =`
🔴 **config.py** (Line 71): `DEMO_PASSWORD ==`
🟡 **debug_login.py** (Line 17): `bharath`
🟡 **debug_login.py** (Line 21): `bharath`
🟡 **debug_login.py** (Line 21): `bharath`
🟡 **debug_login.py** (Line 23): `bharath`
🟡 **debug_login.py** (Line 24): `bharath`
🟡 **debug_login.py** (Line 27): `bharath`
🟡 **debug_login.py** (Line 27): `bharath`
🟡 **debug_login.py** (Line 30): `bharath`
🟡 **debug_login.py** (Line 30): `bharath`
🟡 **debug_login.py** (Line 45): `bharath`
🟡 **debug_login.py** (Line 46): `bharath`
🟡 **debug_login.py** (Line 80): `bharath`
🟡 **debug_login.py** (Line 80): `bharath`
🟡 **debug_login.py** (Line 83): `bharath`
🟡 **debug_login.py** (Line 84): `bharath`
🟡 **debug_login.py** (Line 91): `bharath`
🟡 **debug_login.py** (Line 97): `bharath`
🟡 **debug_login.py** (Line 98): `bharath`
🔴 **deep_investigation.py** (Line 144): `password = "DemoUserPassword123!"`
🔴 **deep_investigation.py** (Line 144): `Password123`
🔴 **deep_investigation.py** (Line 144): `demo_password =`
🟡 **deep_investigation.py** (Line 29): `bharath`
🟡 **deep_investigation.py** (Line 33): `bharath`
🟡 **deep_investigation.py** (Line 39): `bharath`
🟡 **deep_investigation.py** (Line 132): `bharath`
🟡 **deep_investigation.py** (Line 133): `BHARATH`
🟡 **deep_investigation.py** (Line 136): `bharath`
🟡 **deep_investigation.py** (Line 138): `bharath`
🟡 **deep_investigation.py** (Line 141): `bharath`
🟡 **deep_investigation.py** (Line 146): `bharath`
🟡 **deep_investigation.py** (Line 153): `bharath`
🟡 **deep_investigation.py** (Line 154): `bharath`
🟡 **deep_investigation.py** (Line 155): `bharath`
🟡 **deploy_azure_secure.py** (Line 40): `bharath`
🟡 **deploy_azure_secure.py** (Line 41): `bharath`
🟡 **deploy_azure_secure.py** (Line 161): `bharath`
🟡 **deploy_azure_secure.py** (Line 162): `bharath`
🟡 **deploy_azure_secure.py** (Line 164): `bharath`
🟡 **deploy_azure_secure.py** (Line 9): `hardcoded`
🟡 **deploy_azure_secure.py** (Line 98): `hardcoded`
🟡 **deploy_azure_secure.py** (Line 99): `hardcoded`
🟡 **deploy_azure_secure.py** (Line 100): `hardcoded`
🟡 **deploy_azure_secure.py** (Line 106): `Hardcoded`
🟡 **deploy_azure_secure.py** (Line 107): `Hardcoded`
🟡 **deploy_azure_secure.py** (Line 109): `Hardcoded`
🟡 **deploy_azure_secure.py** (Line 142): `hardcoded`
🟡 **deploy_azure_secure.py** (Line 236): `hardcoded`
🟡 **deploy_azure_secure.py** (Line 282): `hardcoded`
🟡 **deploy_secure.py** (Line 40): `bharath`
🟡 **deploy_secure.py** (Line 41): `bharath`
🟡 **deploy_secure.py** (Line 164): `bharath`
🟡 **deploy_secure.py** (Line 165): `bharath`
🟡 **deploy_secure.py** (Line 167): `bharath`
🟡 **deploy_secure.py** (Line 9): `hardcoded`
🟡 **deploy_secure.py** (Line 98): `hardcoded`
🟡 **deploy_secure.py** (Line 99): `hardcoded`
🟡 **deploy_secure.py** (Line 100): `hardcoded`
🟡 **deploy_secure.py** (Line 106): `Hardcoded`
🟡 **deploy_secure.py** (Line 107): `Hardcoded`
🟡 **deploy_secure.py** (Line 109): `Hardcoded`
🟡 **deploy_secure.py** (Line 145): `hardcoded`
🟡 **deploy_secure.py** (Line 239): `hardcoded`
🟡 **deploy_secure.py** (Line 285): `hardcoded`
🟡 **detailed_login_test.py** (Line 9): `bharath`
🟡 **detailed_login_test.py** (Line 25): `bharath`
🟡 **detailed_login_test.py** (Line 28): `bharath`
🟡 **detailed_login_test.py** (Line 29): `bharath`
🟡 **detailed_login_test.py** (Line 32): `bharath`
🟡 **detailed_login_test.py** (Line 32): `bharath`
🟡 **detailed_login_test.py** (Line 38): `bharath`
🟡 **detailed_login_test.py** (Line 38): `bharath`
🔴 **env_manager.py** (Line 44): `ADMIN_PASSWORD') ==`
🔴 **env_manager.py** (Line 47): `DEMO_PASSWORD') ==`
🟡 **env_manager.py** (Line 56): `bharath`
🟡 **final_error_check.py** (Line 39): `bharath`
🟡 **final_validation.py** (Line 97): `bharath`
🟡 **final_validation.py** (Line 97): `bharath`
🟡 **final_validation.py** (Line 98): `bharath`
🟡 **final_validation.py** (Line 99): `bharath`
🟡 **final_validation.py** (Line 102): `bharath`
🟡 **final_validation.py** (Line 103): `bharath`
🟡 **final_validation.py** (Line 122): `bharath`
🟡 **final_validation.py** (Line 127): `bharath`
🟡 **final_validation.py** (Line 133): `bharath`
🟡 **final_verification.py** (Line 31): `bharath`
🟡 **fix_bharath_login.py** (Line 3): `bharath`
🟡 **fix_bharath_login.py** (Line 11): `bharath`
🟡 **fix_bharath_login.py** (Line 12): `bharath`
🟡 **fix_bharath_login.py** (Line 13): `BHARATH`
🟡 **fix_bharath_login.py** (Line 19): `bharath`
🟡 **fix_bharath_login.py** (Line 20): `bharath`
🟡 **fix_bharath_login.py** (Line 20): `bharath`
🟡 **fix_bharath_login.py** (Line 22): `bharath`
🟡 **fix_bharath_login.py** (Line 23): `bharath`
🟡 **fix_bharath_login.py** (Line 26): `bharath`
🟡 **fix_bharath_login.py** (Line 26): `bharath`
🟡 **fix_bharath_login.py** (Line 27): `bharath`
🟡 **fix_bharath_login.py** (Line 28): `bharath`
🟡 **fix_bharath_login.py** (Line 29): `bharath`
🟡 **fix_bharath_login.py** (Line 30): `bharath`
🟡 **fix_bharath_login.py** (Line 32): `bharath`
🟡 **fix_bharath_login.py** (Line 33): `bharath`
🟡 **fix_bharath_login.py** (Line 33): `bharath`
🟡 **fix_bharath_login.py** (Line 34): `bharath`
🟡 **fix_bharath_login.py** (Line 36): `bharath`
🟡 **fix_bharath_login.py** (Line 37): `bharath`
🟡 **fix_bharath_login.py** (Line 39): `bharath`
🟡 **fix_bharath_login.py** (Line 41): `bharath`
🟡 **fix_bharath_login.py** (Line 47): `bharath`
🟡 **fix_bharath_login.py** (Line 48): `bharath`
🟡 **fix_bharath_login.py** (Line 50): `bharath`
🟡 **fix_bharath_login.py** (Line 50): `bharath`
🟡 **fix_bharath_login.py** (Line 57): `bharath`
🟡 **fix_bharath_login.py** (Line 58): `bharath`
🟡 **fix_bharath_login.py** (Line 59): `BHARATH`
🟡 **fix_bharath_login.py** (Line 65): `bharath`
🟡 **fix_bharath_login.py** (Line 65): `bharath`
🟡 **fix_bharath_login.py** (Line 68): `bharath`
🟡 **fix_bharath_login.py** (Line 69): `bharath`
🟡 **fix_bharath_login.py** (Line 114): `bharath`
🟡 **fix_bharath_login.py** (Line 115): `bharath`
🟡 **fix_bharath_password.py** (Line 3): `bharath`
🟡 **fix_bharath_password.py** (Line 3): `bharath`
🟡 **fix_bharath_password.py** (Line 9): `bharath`
🟡 **fix_bharath_password.py** (Line 12): `bharath`
🟡 **fix_bharath_password.py** (Line 12): `bharath`
🟡 **fix_bharath_password.py** (Line 13): `bharath`
🟡 **fix_bharath_password.py** (Line 13): `bharath`
🟡 **fix_bharath_password.py** (Line 15): `bharath`
🟡 **fix_bharath_password.py** (Line 18): `bharath`
🟡 **fix_bharath_password.py** (Line 18): `bharath`
🟡 **fix_bharath_password.py** (Line 22): `bharath`
🟡 **fix_bharath_password.py** (Line 22): `bharath`
🟡 **fix_bharath_password.py** (Line 27): `bharath`
🟡 **fix_bharath_password.py** (Line 30): `bharath`
🟡 **fix_bharath_password.py** (Line 38): `bharath`
🔴 **password_monitor.py** (Line 33): `password = "DemoUserPassword123!"`
🔴 **password_monitor.py** (Line 34): `password = "DemoPass2024!"`
🔴 **password_monitor.py** (Line 134): `PASSWORD = "bharath"`
🔴 **password_monitor.py** (Line 33): `Password123`
🔴 **password_monitor.py** (Line 63): `Password123`
🔴 **password_monitor.py** (Line 33): `demo_password =`
🔴 **password_monitor.py** (Line 34): `demo_password =`
🔴 **password_monitor.py** (Line 150): `demo_password =`
🟡 **password_monitor.py** (Line 3): `Bharath`
🟡 **password_monitor.py** (Line 4): `bharath`
🟡 **password_monitor.py** (Line 22): `bharath`
🟡 **password_monitor.py** (Line 23): `bharath`
🟡 **password_monitor.py** (Line 30): `bharath`
🟡 **password_monitor.py** (Line 45): `bharath`
🟡 **password_monitor.py** (Line 48): `bharath`
🟡 **password_monitor.py** (Line 76): `bharath`
🟡 **password_monitor.py** (Line 94): `Bharath`
🟡 **password_monitor.py** (Line 99): `Bharath`
🟡 **password_monitor.py** (Line 105): `Bharath`
🟡 **password_monitor.py** (Line 123): `Bharath`
🟡 **password_monitor.py** (Line 124): `bharath`
🟡 **password_monitor.py** (Line 130): `bharath`
🟡 **password_monitor.py** (Line 131): `bharath`
🟡 **password_monitor.py** (Line 133): `bharath`
🟡 **password_monitor.py** (Line 134): `BHARATH`
🟡 **password_monitor.py** (Line 134): `bharath`
🟡 **password_monitor.py** (Line 143): `bharath`
🟡 **password_monitor.py** (Line 144): `bharath`
🟡 **password_monitor.py** (Line 154): `bharath`
🟡 **password_monitor.py** (Line 156): `BHARATH`
🟡 **password_monitor.py** (Line 158): `bharath`
🟡 **password_monitor.py** (Line 169): `bharath`
🟡 **password_monitor.py** (Line 174): `Bharath`
🟡 **password_monitor.py** (Line 176): `Bharath`
🟡 **password_monitor.py** (Line 184): `bharath`
🟡 **password_monitor.py** (Line 192): `BHARATH`
🟡 **password_monitor.py** (Line 197): `Bharath`
🟡 **password_monitor.py** (Line 199): `bharath`
🟡 **password_monitor.py** (Line 206): `bharath`
🟡 **persistence_verification_final.py** (Line 31): `bharath`
🟡 **persistence_verification_final.py** (Line 43): `bharath`
🟡 **persistence_verification_final.py** (Line 44): `bharath`
🟡 **persistence_verification_final.py** (Line 45): `bharath`
🟡 **persistence_verification_final.py** (Line 57): `bharath`
🟡 **persistence_verification_final.py** (Line 69): `bharath`
🔴 **prepare_deployment.py** (Line 28): `ADMIN_PASSWORD =`
🔴 **prepare_deployment.py** (Line 30): `DEMO_PASSWORD =`
🟡 **prepare_deployment.py** (Line 37): `bharath`
🟡 **prepare_deployment.py** (Line 109): `bharath`
🔴 **production_config.py** (Line 25): `ADMIN_PASSWORD =`
🔴 **production_config.py** (Line 27): `DEMO_PASSWORD =`
🟡 **refactoring_summary.py** (Line 4): `bharath`
🟡 **refactoring_summary.py** (Line 27): `bharath`
🟡 **refactoring_summary.py** (Line 28): `BHARATH`
🟡 **refactoring_summary.py** (Line 29): `bharath`
🟡 **refactoring_summary.py** (Line 29): `bharath`
🟡 **refactoring_summary.py** (Line 30): `bharath`
🟡 **refactoring_summary.py** (Line 31): `bharath`
🟡 **refactoring_summary.py** (Line 32): `bharath`
🟡 **refactoring_summary.py** (Line 33): `bharath`
🟡 **refactoring_summary.py** (Line 34): `bharath`
🟡 **refactoring_summary.py** (Line 35): `bharath`
🟡 **refactoring_summary.py** (Line 36): `bharath`
🟡 **refactoring_summary.py** (Line 45): `BHARATH`
🟡 **refactoring_summary.py** (Line 54): `BHARATH`
🟡 **refactoring_summary.py** (Line 67): `bharath`
🟡 **refactoring_summary.py** (Line 79): `bharath`
🟡 **refactoring_summary.py** (Line 80): `bharath`
🟡 **refactoring_summary.py** (Line 81): `bharath`
🟡 **refactoring_summary.py** (Line 82): `bharath`
🟡 **refactoring_summary.py** (Line 83): `bharath`
🟡 **refactoring_summary.py** (Line 84): `bharath`
🟡 **refactoring_summary.py** (Line 85): `bharath`
🟡 **refactoring_summary.py** (Line 86): `BHARATH`
🟡 **refactoring_summary.py** (Line 97): `bharath`
🟡 **refactoring_summary.py** (Line 98): `bharath`
🟡 **refactoring_summary.py** (Line 114): `bharath`
🟡 **refactoring_summary.py** (Line 115): `bharath`
🟡 **refactoring_summary.py** (Line 116): `bharath`
🟡 **refactoring_summary.py** (Line 117): `bharath`
🟡 **refactoring_summary.py** (Line 131): `bharath`
🟡 **refactoring_summary.py** (Line 132): `bharath`
🟡 **refactoring_summary.py** (Line 133): `bharath`
🟡 **refactoring_summary.py** (Line 134): `bharath`
🟡 **refactoring_summary.py** (Line 135): `bharath`
🟡 **refactoring_summary.py** (Line 146): `bharath`
🟡 **refactoring_summary.py** (Line 146): `bharath`
🟡 **refactoring_summary.py** (Line 148): `bharath`
🟡 **refactoring_summary.py** (Line 149): `bharath`
🟡 **refactoring_summary.py** (Line 150): `bharath`
🟡 **refactoring_summary.py** (Line 151): `BHARATH`
🟡 **refactoring_summary.py** (Line 158): `bharath`
🟡 **refactoring_summary.py** (Line 27): `hardcoded`
🟡 **refactoring_summary.py** (Line 67): `hardcoded`
🟡 **refactoring_summary.py** (Line 112): `hardcoded`
🔴 **reset_admin_env_password.py** (Line 19): `admin_password =`
🔴 **reset_admin_env_password.py** (Line 23): `ADMIN_PASSWORD=`
🔴 **reset_admin_env_password.py** (Line 95): `admin_password =`
🔴 **reset_admin_env_password.py** (Line 96): `demo_password =`
🔴 **reset_all_passwords.py** (Line 87): `admin_password =`
🔴 **reset_all_passwords.py** (Line 99): `admin_success = reset_user_password('admin', admin_password, 'Admin', explicit_user_request=`
🔴 **reset_all_passwords.py** (Line 88): `demo_password =`
🔴 **reset_all_passwords.py** (Line 102): `demo_success = reset_user_password('demo', demo_password, 'Demo User', explicit_user_request=`
🟡 **reset_bharath.py** (Line 3): `bharath`
🟡 **reset_bharath.py** (Line 3): `bharath`
🟡 **reset_bharath.py** (Line 9): `bharath`
🟡 **reset_bharath.py** (Line 12): `bharath`
🟡 **reset_bharath.py** (Line 13): `bharath`
🟡 **reset_bharath.py** (Line 15): `bharath`
🟡 **reset_bharath.py** (Line 18): `bharath`
🟡 **reset_bharath.py** (Line 22): `bharath`
🟡 **reset_bharath.py** (Line 22): `bharath`
🟡 **reset_bharath.py** (Line 27): `bharath`
🟡 **reset_bharath.py** (Line 32): `bharath`
🟡 **reset_bharath.py** (Line 40): `bharath`
🔴 **safe_password_reset.py** (Line 76): `admin_password =`
🔴 **safe_password_reset.py** (Line 78): `demo_password =`
🟡 **safe_password_reset.py** (Line 13): `bharath`
🟡 **safe_password_reset.py** (Line 100): `bharath`
🟡 **safe_password_reset.py** (Line 101): `bharath`
🟡 **safe_password_reset.py** (Line 107): `bharath`
🟡 **safe_password_reset.py** (Line 114): `bharath`
🟡 **safe_password_reset.py** (Line 119): `bharath`
🔴 **setup_azure_env_vars.py** (Line 20): `Password123`
🔴 **setup_azure_env_vars.py** (Line 22): `Password123`
🟡 **setup_azure_env_vars.py** (Line 38): `bharath`
🟡 **setup_azure_env_vars.py** (Line 47): `bharath`
🟡 **setup_azure_env_vars.py** (Line 73): `bharath`
🟡 **simple_login_debug.py** (Line 41): `bharath`
🟡 **simple_login_debug.py** (Line 42): `bharath`
🟡 **simple_profile_test.py** (Line 35): `bharath`
🟡 **simple_profile_test.py** (Line 36): `bharath`
🟡 **simple_profile_test.py** (Line 36): `bharath`
🟡 **simple_profile_test.py** (Line 38): `bharath`
🟡 **simple_profile_test.py** (Line 39): `bharath`
🟡 **simple_profile_test.py** (Line 43): `bharath`
🟡 **simple_profile_test.py** (Line 43): `bharath`
🟡 **simple_profile_test.py** (Line 50): `bharath`
🟡 **simple_profile_test.py** (Line 66): `bharath`
🟡 **simple_profile_test.py** (Line 76): `bharath`
🟡 **simple_profile_test.py** (Line 77): `bharath`
🟡 **simple_profile_test.py** (Line 92): `bharath`
🔴 **update_azure_passwords.py** (Line 20): `Password123`
🔴 **update_azure_passwords.py** (Line 22): `Password123`
🔴 **update_azure_passwords.py** (Line 20): `admin_password =`
🔴 **update_azure_passwords.py** (Line 22): `demo_password =`
🟡 **update_azure_passwords.py** (Line 77): `bharath`
🟡 **update_azure_passwords.py** (Line 77): `bharath`
🟡 **update_azure_passwords.py** (Line 77): `bharath`
🟡 **validate_user_management.py** (Line 4): `bharath`
🟡 **validate_user_management.py** (Line 17): `bharath`
🟡 **validate_user_management.py** (Line 35): `bharath`
🟡 **validate_user_management.py** (Line 38): `bharath`
🟡 **validate_user_management.py** (Line 39): `bharath`
🟡 **validate_user_management.py** (Line 40): `bharath`
🟡 **validate_user_management.py** (Line 42): `bharath`
🟡 **validate_user_management.py** (Line 43): `bharath`
🟡 **validate_user_management.py** (Line 56): `bharath`
🟡 **validate_user_management.py** (Line 57): `bharath`
🟡 **validate_user_management.py** (Line 59): `bharath`
🟡 **validate_user_management.py** (Line 62): `bharath`
🟡 **validate_user_management.py** (Line 63): `bharath`
🟡 **validate_user_management.py** (Line 65): `bharath`
🟡 **validate_user_management.py** (Line 68): `bharath`
🟡 **validate_user_management.py** (Line 69): `bharath`
🟡 **validate_user_management.py** (Line 71): `bharath`
🟡 **validate_user_management.py** (Line 100): `bharath`
🟡 **validate_user_management.py** (Line 101): `bharath`
🟡 **validate_user_management.py** (Line 115): `BHARATH`
🟡 **validate_user_management.py** (Line 116): `BHARATH`
🟡 **validate_user_management.py** (Line 118): `BHARATH`
🟡 **validate_user_management.py** (Line 126): `bharath`
🟡 **validate_user_management.py** (Line 127): `bharath`
🟡 **validate_user_management.py** (Line 142): `bharath`
🟡 **validate_user_management.py** (Line 148): `bharath`
🟡 **validate_user_management.py** (Line 157): `bharath`
🟡 **validate_user_management.py** (Line 158): `bharath`
🟡 **validate_user_management.py** (Line 159): `bharath`
🟡 **validate_user_management.py** (Line 162): `bharath`
🟡 **validate_user_management.py** (Line 180): `bharath`
🟡 **verify_users_after_restart.py** (Line 9): `bharath`
🟡 **verify_users_after_restart.py** (Line 36): `bharath`
🟡 **verify_users_after_restart.py** (Line 37): `bharath`
🟡 **verify_users_after_restart.py** (Line 38): `bharath`
🟡 **verify_users_after_restart.py** (Line 41): `bharath`
🟡 **verify_users_after_restart.py** (Line 60): `bharath`
🟡 **verify_users_after_restart.py** (Line 60): `bharath`
🟡 **.venv\Lib\site-packages\jinja2\meta.py** (Line 64): `hardcoded`
🟡 **.venv\Lib\site-packages\pip\_internal\network\session.py** (Line 465): `hardcoded`
🔴 **.venv\Lib\site-packages\pip\_internal\utils\misc.py** (Line 475): `password = ""`
🔴 **.venv\Lib\site-packages\pip\_internal\utils\misc.py** (Line 478): `password = ":****"`
🔴 **.venv\Lib\site-packages\setuptools\_distutils\dist.py** (Line 207): `password = ''`
🔴 **.venv\Lib\site-packages\setuptools\_distutils\command\register.py** (Line 143): `password = ''`
🔴 **.venv\Lib\site-packages\setuptools\_distutils\command\upload.py** (Line 43): `password = ''`

## Deployment Recommendations

1. **❌ BLOCK DEPLOYMENT**: Review and secure dangerous operations
2. **🔐 Fix Credentials**: Replace hardcoded credentials with environment variables
3. **✅ Verify Security Guards**: Ensure all user operations are protected
4. **🧪 Run Tests**: Execute all security tests before deployment
5. **📝 Document Changes**: Update deployment documentation