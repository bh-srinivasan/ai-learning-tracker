# Azure SQL Database Connection Guide

## Overview
This document outlines all the files, configurations, and code used to establish connection with Azure SQL Database in the AI Learning Tracker application.

## 📁 Files Involved in Azure SQL Connection

### 1. **Main Application File**
- **File**: `app.py`
- **Purpose**: Contains the core database connection logic
- **Key Functions**:
  - `is_azure_sql()` - Checks if Azure SQL environment variables are set
  - `get_db_connection()` - Main connection dispatcher
  - `_get_azure_sql_connection()` - Azure SQL specific connection logic
  - `_wrap_azure_sql_connection()` - Compatibility wrapper for SQLite-like interface

### 2. **Environment Configuration Files**
- **File**: `.env.database.azure`
- **Purpose**: Azure production environment configuration template
- **Contains**: Environment variable references for Azure App Service

### 3. **Test Files**
- **File**: `test_azure_sql.py`
- **Purpose**: Test Azure SQL connection independently
- **File**: `check_azure_env.py`
- **Purpose**: Check Azure environment variables from deployed app
- **File**: `azure_sql_connection.py`
- **Purpose**: Extracted connection code for reference

### 4. **Dependencies**
- **File**: `requirements.txt`
- **Key Package**: `pyodbc==4.0.39` - ODBC driver for SQL Server

## 🔧 Environment Variables Required

### Azure App Service Configuration
These must be set in Azure Portal > App Services > Configuration > Application settings:

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `ENV` | `production` | Environment indicator |
| `AZURE_SQL_SERVER` | `ai-learning-sql-centralus.database.windows.net` | Azure SQL Server hostname |
| `AZURE_SQL_DATABASE` | `ai-learning-db` | Database name |
| `AZURE_SQL_USERNAME` | `ailearningadmin` | Database username |
| `AZURE_SQL_PASSWORD` | `[secure-password]` | Database password |
| `ADMIN_PASSWORD` | `[admin-password]` | Application admin password |

## 📝 Connection Process Step-by-Step

### Step 1: Environment Variable Check
```python
def is_azure_sql():
    """Check if all Azure SQL environment variables are set"""
    azure_server = os.environ.get('AZURE_SQL_SERVER')
    azure_database = os.environ.get('AZURE_SQL_DATABASE')
    azure_username = os.environ.get('AZURE_SQL_USERNAME')
    azure_password = os.environ.get('AZURE_SQL_PASSWORD')
    
    return all([azure_server, azure_database, azure_username, azure_password])
```

### Step 2: Connection String Construction
```python
azure_connection_string = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server=tcp:{azure_server},1433;"
    f"Database={azure_database};"
    f"Uid={azure_username};"
    f"Pwd={azure_password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)
```

### Step 3: Connection Establishment
```python
import pyodbc
conn = pyodbc.connect(azure_connection_string)
```

### Step 4: Compatibility Wrapper
The connection is wrapped to provide SQLite-like interface for code compatibility:
- `SimpleRow` class for row access
- `AzureSQLConnection` class for connection management
- `AzureSQLCursor` class for cursor operations

## 🔍 Connection Testing

### Debug Endpoints Available
1. **`/debug/env`** - Check environment variables status
2. **`/debug/db-test`** - Test database connection with detailed results

### Test Results (From Azure Deployment)
```json
{
  "environment": "production",
  "tests": [
    {
      "name": "Environment Variables",
      "status": "PASS",
      "details": {"message": "All Azure SQL environment variables are set"}
    },
    {
      "name": "Database Connection", 
      "status": "PASS",
      "details": {"message": "Database connection successful"}
    },
    {
      "name": "Database Query",
      "status": "PASS", 
      "details": {"message": "Query successful, 2 users found"}
    }
  ]
}
```

## 📊 Connection Flow Diagram

```
Application Start
       ↓
Check Environment Variables
   ↓               ↓
Azure SQL      SQLite (fallback)
   ↓
Build Connection String
   ↓
pyodbc.connect()
   ↓
Wrap Connection (compatibility)
   ↓
Return to Application
```

## 🛠️ Configuration in Azure Portal

### Azure App Service Settings Path:
1. Go to **Azure Portal**
2. Navigate to **App Services**
3. Select **ai-learning-tracker-bharath**
4. Go to **Configuration**
5. Under **Application settings**, add:

```
ENV=production
AZURE_SQL_SERVER=ai-learning-sql-centralus.database.windows.net
AZURE_SQL_DATABASE=ai-learning-db
AZURE_SQL_USERNAME=ailearningadmin
AZURE_SQL_PASSWORD=[your-secure-password]
ADMIN_PASSWORD=[your-admin-password]
```

## 🔐 Security Considerations

### Environment Variables
- ✅ No hardcoded passwords in source code
- ✅ Passwords stored in Azure App Service configuration
- ✅ Environment variables properly validated before use
- ✅ Fallback to secure defaults (fail if not set)

### Connection Security
- ✅ Encrypted connection (`Encrypt=yes`)
- ✅ Server certificate verification
- ✅ Connection timeout configured
- ✅ ODBC Driver 17 for SQL Server (latest)

## 📋 Verification Commands

### Check Environment Variables (Azure)
```bash
curl https://ai-learning-tracker-bharath.azurewebsites.net/debug/env
```

### Test Database Connection (Azure)
```bash
curl https://ai-learning-tracker-bharath.azurewebsites.net/debug/db-test
```

### Local Testing
```bash
python azure_sql_connection.py
python check_env_vars.py
```

## 🚨 Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Environment variables not set | Missing Azure App Service config | Add variables in Azure Portal |
| Connection timeout | Firewall/network issue | Check Azure SQL firewall rules |
| Authentication failed | Wrong credentials | Verify username/password in Azure |
| Driver not found | Missing ODBC driver | Ensure `pyodbc` is installed |

### Error Handling
The application includes comprehensive error handling:
- Environment variable validation
- Connection failure handling
- Graceful fallback to SQLite for local development
- Detailed error logging

## 📈 Current Status

### ✅ Working Components
- Environment variables properly set in Azure
- Database connection established successfully
- Query execution working
- 2 users found in database

### ❌ Outstanding Issues
- Admin routes not loading (separate from DB connection)
- Login returns 500 error (application logic issue, not DB)

The Azure SQL Database connection is **fully functional**. Any remaining issues are in the application logic layer, not the database connectivity.

## 🔗 Related Files

- `app.py` (lines 90-320) - Main connection logic
- `.env.database.azure` - Environment configuration
- `requirements.txt` - Dependencies
- `azure_sql_connection.py` - Extracted connection code
- `check_azure_env.py` - Environment validation
- `test_azure_sql.py` - Connection testing
