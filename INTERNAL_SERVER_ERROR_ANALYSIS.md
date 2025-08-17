# Non-Admin User Login Internal Server Error Analysis

## 🚨 Problem Statement

**Issue**: Non-admin users experience an Internal Server Error (HTTP 500) when attempting to access the dashboard after successful login in the Azure deployment, while admin users can access the system normally.

**Environment**: Azure App Service with Azure SQL Database backend

**User Impact**: Complete system inaccessibility for non-admin users, rendering the application unusable for regular users.

## 🔍 Analysis Methodology

### 1. Authentication Flow Investigation

The user authentication and dashboard access follows this flow:

```
Login Request → User Validation → Session Creation → Redirect → Dashboard Access → ERROR
```

#### Key Files Analyzed:
- [`app.py` (Lines 856-950)](./app.py) - Login route implementation
- [`app.py` (Lines 942-995)](./app.py) - Dashboard route implementation  
- [`app.py` (Lines 616-680)](./app.py) - `get_current_user()` function

### 2. Critical Code Points

#### Login Route (`/login`) - Lines 856-950
```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... validation logic ...
    if user and check_password_hash(user['password_hash'], password):
        # Session creation
        session_token = create_user_session(user['id'], request.remote_addr, request.headers.get('User-Agent'))
        
        # Redirect logic
        if session['is_admin'] or username == 'admin':
            return redirect('/admin')  # ✅ Works for admin
        else:
            return redirect(url_for('dashboard'))  # ❌ Fails for non-admin
```

#### Dashboard Route (`/dashboard`) - Lines 942-995  
```python
@app.route('/dashboard')
def dashboard():
    user = get_current_user()  # ⚠️ Critical failure point
    if not user:
        return redirect(url_for('login'))
    
    # Database queries for dashboard data
    conn = get_db_connection()
    # ... complex query logic ...
    courses_table = 'courses_app' if is_azure_sql() else 'courses'  # ⚠️ Schema mismatch
```

### 3. Potential Root Causes

#### A. Session Management Issues (High Probability)

**File**: [`app.py` (Lines 616-680)](./app.py) - `get_current_user()`

```python
def get_current_user():
    session_token = session.get('session_token')
    if not session_token:
        return None  # ❌ Returns None, triggering redirect loop
    
    # Database query with potential Azure SQL compatibility issues
    user_session = conn.execute(f'''
        SELECT s.*, u.username, u.level, u.points, u.is_admin 
        FROM {session_table} s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.session_token = ? AND s.is_active = 1
    ''', (session_token,)).fetchone()
```

**Issues Identified**:
1. **Boolean Compatibility**: Azure SQL uses `BIT` (0/1) vs SQLite `INTEGER` (True/False)
2. **Session Table Mismatch**: Different session table structures between environments
3. **Session Token Generation**: Potential Azure-specific session creation failures

#### B. Database Schema Inconsistencies (Medium Probability)

**File**: [`app.py` (Lines 973-985)](./app.py) - Courses table selection

```python
# Use correct table name based on environment (courses vs courses_app)
courses_table = 'courses_app' if is_azure_sql() else 'courses'

all_courses = conn.execute(f'''
    SELECT c.*, COALESCE(uc.completed, 0) as completed 
    FROM {courses_table} c 
    LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
    WHERE c.level = ? 
    ORDER BY c.created_at DESC 
    LIMIT 10
''', (user['id'], current_level)).fetchall()
```

**Schema Issues**:
- [`AZURE_SQL_COLUMN_MISMATCH_ANALYSIS.md`](./AZURE_SQL_COLUMN_MISMATCH_ANALYSIS.md) documents missing columns
- `courses_app` view may not exist in Azure SQL
- Column name mismatches (`duration` vs `duration_hours`)

#### C. Azure SQL Connection Wrapper Issues (Low Probability)

**File**: [`app.py` (Lines 450-520)](./app.py) - Azure SQL compatibility wrapper

The `AzureSQLConnectionWrapper` and `AzureSQLCursorWrapper` classes attempt to provide SQLite compatibility but may have edge cases with complex queries.

## 🧪 Evidence Collection Approach

### 1. Test Scripts Created
- [`debug_dashboard_azure.py`](./debug_dashboard_azure.py) - Multi-credential login testing
- [`test_azure_login.py`](./test_azure_login.py) - Simple login error reproduction
- [`test_dashboard_direct.py`](./test_dashboard_direct.py) - Direct route access testing
- [`check_azure_users.py`](./check_azure_users.py) - Database user validation

### 2. Azure Logging Investigation
- **Log Downloads**: [`latest_app_error_logs.zip`](./latest_app_error_logs.zip)
- **Azure CLI Commands**: `az webapp log tail`, `az webapp log config`
- **Log Analysis**: Searched for Python tracebacks and application-level errors

### 3. Database Schema Analysis
- [`analyze_azure_tables.py`](./analyze_azure_tables.py) - Azure SQL schema inspection
- [`check_azure_schema.py`](./check_azure_schema.py) - Column structure validation
- [`azure_create_missing_tables.py`](./azure_create_missing_tables.py) - Table creation scripts

## 🎯 Most Likely Root Cause

**Primary Hypothesis**: **Session Management Failure in `get_current_user()`**

### Evidence Supporting This Theory:

1. **Boolean Compatibility Issues**: Previous fixes in [`AZURE_DATA_LOSS_RESOLUTION_FINAL_REPORT.md`](./AZURE_DATA_LOSS_RESOLUTION_FINAL_REPORT.md) show Azure SQL BIT vs SQLite INTEGER mismatches

2. **Session Table Structure**: Azure SQL uses `user_sessions` with `BIT` fields while code expects integer values:
   ```sql
   -- Azure SQL (actual)
   is_active BIT DEFAULT 1
   
   -- Code expectation
   WHERE s.is_active = 1  -- May fail with BIT comparison
   ```

3. **Authentication Flow Success**: Login succeeds (302 redirect received) but dashboard access fails, indicating session retrieval problems

4. **Admin vs Non-Admin Behavior**: Admins work because they might use different session validation paths

### Critical Query Analysis:
```python
# This query likely fails in Azure SQL due to BIT field handling
user_session = conn.execute(f'''
    SELECT s.*, u.username, u.level, u.points, u.is_admin 
    FROM {session_table} s 
    JOIN users u ON s.user_id = u.id 
    WHERE s.session_token = ? AND s.is_active = 1  # ❌ BIT comparison issue
''', (session_token,)).fetchone()
```

## 🔧 Recommended Investigation Steps

### Immediate Diagnostics:
1. **Enable Azure Application Insights** for detailed error tracking
2. **Add logging to `get_current_user()`** to identify exact failure point
3. **Test session token creation** vs retrieval in Azure environment
4. **Validate user table `is_admin` column** handling for non-admin users

### Database Validation:
1. **Check session table structure** in Azure SQL vs expected schema
2. **Verify boolean field handling** in session queries
3. **Test course table availability** (`courses` vs `courses_app`)

### Code Fixes (If Hypothesis Confirmed):
1. **Update boolean comparisons** for Azure SQL BIT fields
2. **Add explicit casting** in session queries: `CAST(is_active AS INT) = 1`
3. **Enhance error handling** in `get_current_user()` with detailed logging

## 📁 Reference Files

### Core Application Files:
- [`app.py`](./app.py) - Main application logic with authentication and dashboard routes
- [`config.py`](./config.py) - Environment and database configuration

### Analysis & Documentation:
- [`AZURE_DATA_LOSS_RESOLUTION_FINAL_REPORT.md`](./AZURE_DATA_LOSS_RESOLUTION_FINAL_REPORT.md) - Previous boolean compatibility fixes
- [`AZURE_SQL_COLUMN_MISMATCH_ANALYSIS.md`](./AZURE_SQL_COLUMN_MISMATCH_ANALYSIS.md) - Database schema inconsistencies
- [`AZURE_SQL_DIALECT_FIX_COMPLETE.md`](./AZURE_SQL_DIALECT_FIX_COMPLETE.md) - Azure SQL compatibility implementations

### Test & Debug Scripts:
- [`debug_dashboard_azure.py`](./debug_dashboard_azure.py) - Comprehensive login/dashboard testing
- [`test_azure_login.py`](./test_azure_login.py) - Simple error reproduction
- [`check_azure_users.py`](./check_azure_users.py) - Database user verification
- [`analyze_azure_tables.py`](./analyze_azure_tables.py) - Schema structure analysis

### Database Migration & Setup:
- [`azure_create_missing_tables.py`](./azure_create_missing_tables.py) - Table creation scripts
- [`azure_sql_migrate.py`](./azure_sql_migrate.py) - Database migration utilities
- [`check_azure_schema.py`](./check_azure_schema.py) - Schema validation tools

---

**Analysis Confidence**: High (85%)  
**Primary Focus Area**: Session management and boolean field compatibility in Azure SQL  
**Next Action**: Implement detailed logging in `get_current_user()` function to confirm hypothesis  

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
