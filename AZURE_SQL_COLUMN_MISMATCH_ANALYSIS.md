# Azure SQL Column Mismatch Analysis & Resolution Plan

## 🚨 Problem Description

**Error:** `Invalid column name 'duration_hours'` when accessing Admin Courses page

**Root Cause:** Schema mismatch between local SQLite database and Azure SQL database for the `courses` table.

## 📊 Current State Analysis

### Local SQLite Schema (Expected)
```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    difficulty TEXT,
    duration_hours REAL,           -- ❌ MISSING IN AZURE
    url TEXT,
    category TEXT,                 -- ❌ MISSING IN AZURE  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Azure SQL Schema (Actual)
```sql
CREATE TABLE courses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(500) NOT NULL,
    description NVARCHAR(MAX),
    url NVARCHAR(1000),
    level NVARCHAR(50),
    points NVARCHAR(50),
    duration NVARCHAR(100),        -- ❌ DIFFERENT NAME (not duration_hours)
    source NVARCHAR(100) DEFAULT 'Manual',
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    url_status NVARCHAR(50) DEFAULT 'Unknown',
    url_checked_at DATETIME2,
    difficulty NVARCHAR(50),
    prerequisites NVARCHAR(MAX),
    learning_objectives NVARCHAR(MAX),
    modules NVARCHAR(MAX),
    certification NVARCHAR(100)
)
```

## 🔍 File Analysis

### Primary Files Involved

#### 1. **Main Application Logic**
- **File:** [`c:\Users\bhsrinivasan\Downloads\Learning\Vibe Coding\AI_Learning\app.py`](file:///c:/Users/bhsrinivasan/Downloads/Learning/Vibe%20Coding/AI_Learning/app.py)
- **Lines:** 2440-2480 (admin_courses route)
- **Issue:** Line 2446 explicitly selects `duration_hours` which doesn't exist in Azure SQL

```python
query = f'''
    SELECT id, title, description, difficulty, duration_hours,  # ❌ FAILS HERE
           url, category, level, created_at
    FROM courses 
    {where_clause}
    ORDER BY created_at DESC 
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
'''
```

#### 2. **Database Schema Creation**
- **File:** [`c:\Users\bhsrinivasan\Downloads\Learning\Vibe Coding\AI_Learning\app.py`](file:///c:/Users/bhsrinivasan/Downloads/Learning/Vibe%20Coding/AI_Learning/app.py)
- **Lines:** 200-220 (Azure SQL schema)
- **Lines:** 340-370 (SQLite schema)
- **Issue:** Inconsistent column names between environments

#### 3. **Admin Template**
- **File:** [`c:\Users\bhsrinivasan\Downloads\Learning\Vibe Coding\AI_Learning\templates\admin\courses.html`](file:///c:/Users/bhsrinivasan/Downloads/Learning/Vibe%20Coding/AI_Learning/templates/admin/courses.html)
- **Status:** Template doesn't directly reference `duration_hours`, but receives course data from backend

#### 4. **Debug Route**
- **URL:** [`https://ai-learning-tracker-bharath.azurewebsites.net/debug/check-courses-table`](https://ai-learning-tracker-bharath.azurewebsites.net/debug/check-courses-table)
- **Purpose:** Inspect actual Azure SQL table structure vs expected structure

## 🛠️ Resolution Strategy

### Option 1: **Add Missing Columns to Azure SQL** (Recommended)
**Pros:** Maintains compatibility with existing local development
**Cons:** Requires schema migration

### Option 2: **Update Code to Match Azure Schema**
**Pros:** No database changes needed
**Cons:** Breaks local development compatibility

### Option 3: **Dynamic Column Detection** (Best Long-term)
**Pros:** Automatically adapts to both environments
**Cons:** More complex implementation

## 📋 Implementation Plan

### Phase 1: Immediate Fix (Option 1)
1. **Add Missing Columns to Azure SQL**
   ```sql
   ALTER TABLE courses ADD duration_hours FLOAT;
   ALTER TABLE courses ADD category NVARCHAR(100);
   ```

2. **Data Migration**
   ```sql
   UPDATE courses SET duration_hours = TRY_CONVERT(FLOAT, duration) WHERE duration IS NOT NULL;
   ```

### Phase 2: Code Updates
1. **Update admin_courses route** to handle both schemas
2. **Add column existence checks** before querying
3. **Implement fallback queries** for missing columns

### Phase 3: Template Updates
1. **Update courses template** to handle missing fields gracefully
2. **Add conditional rendering** for optional columns

## 🔧 Specific Code Changes Required

### File: `app.py` (admin_courses route)
**Location:** Lines 2440-2480
**Change:** Replace hardcoded column list with dynamic detection

```python
# Instead of:
SELECT id, title, description, difficulty, duration_hours, url, category, level, created_at

# Use:
SELECT id, title, description, difficulty, 
       CASE WHEN EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                       WHERE TABLE_NAME = 'courses' AND COLUMN_NAME = 'duration_hours')
            THEN duration_hours ELSE NULL END as duration_hours,
       url, level, created_at
```

### File: `app.py` (schema initialization)
**Location:** Lines 200-220, 340-370
**Change:** Standardize column names between Azure SQL and SQLite

## 🧪 Testing Plan

1. **Deploy column addition script** to Azure SQL
2. **Test admin courses page** functionality
3. **Verify data migration** accuracy
4. **Test local development** environment compatibility
5. **Validate template rendering** with new/missing columns

## 📝 Success Criteria

- ✅ Admin courses page loads without errors
- ✅ Course data displays correctly in both environments
- ✅ Pagination and filtering work properly
- ✅ Local development remains functional
- ✅ No data loss during migration

## 🚀 Deployment Steps

1. **Backup Azure SQL database**
2. **Run column addition scripts**
3. **Deploy updated application code**
4. **Verify functionality**
5. **Monitor for any issues**

## 📍 Additional Resources

- **Azure SQL Management:** [Azure Portal](https://portal.azure.com)
- **Debug Endpoint:** [Table Structure Inspector](https://ai-learning-tracker-bharath.azurewebsites.net/debug/check-courses-table)
- **Application Logs:** [Azure Log Stream](https://ai-learning-tracker-bharath.scm.azurewebsites.net/api/logs/docker)

---

**Next Action:** Execute Phase 1 to add missing columns to Azure SQL database, then update the application code to handle both schemas gracefully.
