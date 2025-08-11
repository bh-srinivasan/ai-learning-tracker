# Azure Admin Password Change Functionality - Complete File Analysis

## Overview
You're experiencing a "Method Not Allowed" error when trying to change the admin password in Azure. This indicates a routing issue where the current route only supports GET requests but the form is trying to POST.

## Root Cause
The current `admin_change_password()` function in [`app.py`](app.py) **only supports GET requests** but the form needs to POST data.

### Current Implementation (BROKEN)
```python
# File: app.py (lines 2443-2452)
@app.route('/admin/change-password')  # ❌ Only GET method allowed
def admin_change_password():
    """Admin password change page"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Password change page (placeholder implementation)
    return render_template('admin/change_password.html')
```

### Working Implementation (FROM BACKUP)
```python
# File: app_backup.py (lines 3301-3332)
@app.route('/admin/change-password', methods=['GET', 'POST'])  # ✅ Both methods supported
def admin_change_password():
    """Admin change password"""
    user = get_current_user()
    if not user or user['username'] != 'admin':
        flash('Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('admin/change_password.html')
        
        # Verify current password
        conn = get_db_connection()
        try:
            admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
            if admin_user and check_password_hash(admin_user['password_hash'], current_password):
                # Update password
                new_hash = generate_password_hash(new_password)
                conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
                conn.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Current password is incorrect.', 'error')
        finally:
            conn.close()
    
    return render_template('admin/change_password.html')
```

## Files Involved in Admin Password Change

### 1. Backend Route
- **File:** [`app.py`](app.py) (lines 2443-2452)
- **Issue:** Missing POST method support and password change logic
- **Status:** ❌ BROKEN - Only placeholder implementation

### 2. Template File
- **File:** [`templates/admin/change_password.html`](templates/admin/change_password.html)
- **Purpose:** HTML form for password change
- **Status:** ✅ WORKING - Contains proper form with POST method

### 3. Backup Reference
- **File:** [`app_backup.py`](app_backup.py) (lines 3301-3332)
- **Purpose:** Contains the correct working implementation
- **Status:** ✅ WORKING - Full implementation with POST handling

## Required Files for Azure Deployment

### Core Files
1. **Main Application:** [`app.py`](app.py) - Needs the route fix
2. **Template:** [`templates/admin/change_password.html`](templates/admin/change_password.html) - Already correct
3. **Base Template:** [`templates/base.html`](templates/base.html) - For layout inheritance

### Dependencies
- **Flask imports:** `request`, `flash`, `redirect`, `url_for`, `render_template`
- **Security functions:** `check_password_hash`, `generate_password_hash` (from `werkzeug.security`)
- **Database function:** `get_db_connection()`
- **User function:** `get_current_user()`

## Solution Steps

### Step 1: Fix the Route Definition
Replace the current route in [`app.py`](app.py) at line 2443:

```python
# REPLACE THIS:
@app.route('/admin/change-password')

# WITH THIS:
@app.route('/admin/change-password', methods=['GET', 'POST'])
```

### Step 2: Add POST Logic
Replace the function body with the complete implementation from [`app_backup.py`](app_backup.py).

### Step 3: Test Flow
1. **GET Request:** Shows the form
2. **POST Request:** Processes the password change
3. **Validation:** Checks current password before updating
4. **Success:** Redirects to admin dashboard
5. **Error:** Shows error message and stays on form

## Security Features (Already in Template)
- Current password verification
- Password confirmation matching
- Secure form handling
- Auto-complete attributes for password managers
- CSRF protection (if enabled in Flask)

## Navigation Integration
- Accessible from admin dashboard via "Change Password" link
- Uses `{{ url_for('admin_change_password') }}` in templates
- Back button returns to admin dashboard

## Database Impact
- Updates `users` table
- Field: `password_hash`
- Condition: `username = 'admin'`
- Uses `generate_password_hash()` for secure hashing

## Quick Fix Command
The issue can be fixed by copying the working implementation from the backup file to the main application file.
