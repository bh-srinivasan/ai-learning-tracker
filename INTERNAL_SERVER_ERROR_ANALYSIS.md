# Internal Server Error Analysis - Non-Admin Login Issue

## Executive Summary

**Issue**: Non-admin users are experiencing Internal Server Error during login while admin users can login successfully.

**Status**: ❌ CRITICAL - Non-admin users cannot access the application  
**Environment**: Azure SQL Database vs Local SQLite differences  
**Root Cause**: Azure SQL session/user table schema or query compatibility issues  

## Key Findings

### ✅ Local Environment Analysis
- **Database**: SQLite (`ai_learning.db`)
- **Session Table**: `sessions`
- **Users Found**: 16 total (1 admin, 15 non-admin)
- **Authentication Flow**: ✅ WORKING
- **Session Creation**: ✅ WORKING
- **Test Result**: Non-admin login works perfectly locally

### ❌ Azure Environment Issues
- **Database**: Azure SQL (`ai-learning-sql-centralus.database.windows.net`)
- **Session Table**: `user_sessions` (different from local)
- **Authentication Flow**: ❌ FAILING for non-admin users
- **Admin Login**: ✅ WORKING
- **Test Result**: Non-admin login causes Internal Server Error

## Technical Analysis

### 1. Database Schema Differences

#### Local SQLite Schema:
```sql
-- sessions table (local)
id INTEGER PRIMARY KEY
user_id INTEGER
session_token VARCHAR(255)
created_at TIMESTAMP
expires_at TIMESTAMP
ip_address VARCHAR(45)
user_agent TEXT
is_active BOOLEAN

-- users table (local)
id INTEGER PRIMARY KEY
username TEXT
is_admin INTEGER  -- SQLite uses INTEGER for boolean
```

#### Azure SQL Schema:
```sql
-- user_sessions table (Azure)
id INTEGER PRIMARY KEY
user_id INTEGER
session_token TEXT
created_at TIMESTAMP
expires_at TIMESTAMP
ip_address TEXT
user_agent TEXT
is_active BOOLEAN

-- users table (Azure)
id INTEGER PRIMARY KEY
username TEXT
is_admin BIT  -- Azure SQL uses BIT for boolean
```

### 2. Authentication Flow Analysis

#### Working Flow (Local):
1. ✅ Login POST → `app.py:856`
2. ✅ Password validation
3. ✅ `create_user_session()` → `sessions` table
4. ✅ Session token generation
5. ✅ Redirect based on `is_admin` field

#### Failing Flow (Azure):
1. ✅ Login POST → `app.py:856`
2. ✅ Password validation (admin works)
3. ❌ `create_user_session()` → `user_sessions` table issue
4. ❌ Internal Server Error for non-admin users
5. ❌ Session creation fails or redirect logic fails

### 3. Code Analysis

#### Session Table Detection (`app.py:555`):
```python
def get_session_table():
    """Get appropriate session table name based on environment"""
    return 'user_sessions' if is_azure_sql() else 'sessions'
```

#### Session Creation (`app.py:568`):
```python
def create_user_session(user_id, ip_address, user_agent):
    session_table = get_session_table()  # Returns 'user_sessions' for Azure
    
    # Issue likely here - Azure SQL vs SQLite differences
    if is_azure_sql():
        conn.execute(f'''INSERT INTO {session_table} ...''')
    else:
        conn.execute(f'''INSERT INTO {session_table} ...''')
```

#### User Query (`app.py:628`):
```python
def get_current_user():
    user_session = conn.execute(f'''
        SELECT s.*, u.username, u.level, u.points, u.is_admin 
        FROM {session_table} s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.session_token = ? AND s.is_active = ?
    ''', (session_token, True)).fetchone()
```

## Problem Hypotheses

### Hypothesis 1: Boolean Type Mismatch
- **Local**: `is_admin INTEGER` (0/1)
- **Azure**: `is_admin BIT` (True/False)
- **Impact**: Query `WHERE s.is_active = ?` with `True` parameter may fail

### Hypothesis 2: Session Table Schema Differences
- **Local**: `sessions` table with VARCHAR(255) for session_token
- **Azure**: `user_sessions` table with TEXT for session_token
- **Impact**: Column type differences causing insertion failures

### Hypothesis 3: Transaction Handling
- **Local**: SQLite auto-commit behavior
- **Azure**: Azure SQL requires explicit transaction management
- **Impact**: Session creation rollback for non-admin users

### Hypothesis 4: Connection Pool Issues
- **Local**: Simple SQLite file connection
- **Azure**: Azure SQL connection with potential timeout/pool issues
- **Impact**: Connection drops during non-admin user processing

## Required Actions

### Immediate Investigation (Priority 1)
1. **Enable Azure SQL Debug Logging**
   ```python
   # Add to app.py login route
   logging.basicConfig(level=logging.DEBUG)
   logger.debug(f"Login attempt: user_id={user_id}, is_admin={user.is_admin}")
   ```

2. **Test Schema Compatibility**
   ```python
   # Test user_sessions table structure on Azure
   SELECT TOP 1 * FROM user_sessions;
   SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_NAME = 'user_sessions';
   ```

3. **Monitor Azure SQL Query Execution**
   - Check Azure SQL query performance insights
   - Monitor failed queries in Azure portal
   - Review deadlock and timeout logs

### Targeted Fixes (Priority 2)

#### Fix 1: Boolean Type Compatibility
**File**: `app.py:628` (get_current_user function)
```python
# Change from:
WHERE s.is_active = ?
# To:
WHERE s.is_active = 1  # or CAST(? AS BIT) for Azure SQL
```

#### Fix 2: Enhanced Error Handling
**File**: `app.py:856` (login route)
```python
try:
    session_token = create_user_session(user.id, request.remote_addr, request.headers.get('User-Agent'))
    if not session_token:
        logger.error(f"Session creation failed for user {user.username}")
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('login'))
except Exception as e:
    logger.error(f"Login error for user {user.username}: {e}")
    flash('Login failed. Please contact support.', 'error')
    return redirect(url_for('login'))
```

#### Fix 3: Azure SQL Session Insertion
**File**: `app.py:568` (create_user_session function)
```python
if is_azure_sql():
    # Use explicit column list and proper type casting
    conn.execute(f'''
        INSERT INTO {session_table} (session_token, user_id, ip_address, user_agent, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_token, user_id, ip_address, user_agent, expires_at, 1))
```

## File References

### Core Authentication Files
- **Main Application**: [`app.py`](./app.py) - Lines 856-920 (login route), 568-615 (session creation), 616-680 (user retrieval)
- **Configuration**: [`config.py`](./config.py) - Database connection settings
- **Database Utilities**: [`check_db.py`](./check_db.py) - Schema validation tools

### Debug and Analysis Files
- **Schema Checker**: [`check_db_schema.py`](./check_db_schema.py) - Database schema analysis
- **Login Debugger**: [`debug_non_admin_login.py`](./debug_non_admin_login.py) - Local authentication testing
- **User Checker**: [`check_users_table.py`](./check_users_table.py) - User table validation

### Azure Specific Files
- **Azure Configuration**: [`azure_config_fix.py`](./azure_config_fix.py) - Azure SQL connection fixes
- **Database Investigation**: [`azure_database_investigation.py`](./azure_database_investigation.py) - Azure SQL debugging
- **Environment Fix**: [`azure_env_fix.py`](./azure_env_fix.py) - Environment variable setup

## Success Criteria

### ✅ Validation Tests
1. **Admin Login**: Must continue working on Azure SQL
2. **Non-Admin Login**: Must work without Internal Server Error
3. **Session Creation**: Must work for both user types on Azure SQL
4. **Dashboard Access**: Must work for both user types after login

### 📊 Monitoring Points
1. **Azure SQL Query Performance**: Monitor execution times
2. **Error Logs**: Track authentication failures
3. **Session Table**: Monitor successful session insertions
4. **User Experience**: Confirm seamless login for all users

## Next Steps

1. **Deploy Debug Logging** to Azure SQL environment
2. **Test Boolean Compatibility** fixes for `is_active` field
3. **Implement Enhanced Error Handling** for better diagnostics
4. **Validate Session Creation** on Azure SQL for non-admin users
5. **Monitor Production Logs** for detailed error messages

---
**Document Status**: ACTIVE INVESTIGATION  
**Last Updated**: August 16, 2025  
**Assigned**: GitHub Copilot Analysis  
**Priority**: CRITICAL - Production Issue
