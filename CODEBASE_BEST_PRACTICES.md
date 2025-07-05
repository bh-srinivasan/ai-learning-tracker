# Codebase Best Practices & Maintenance Guide

## 🔒 Critical Security Rules - NEVER VIOLATE

### 1. User Deletion Protection
```python
# CRITICAL RULE: Only admin user is protected from deletion
protected_users = ['admin']  # Do NOT add other users here

# ALWAYS require explicit UI action for user deletion:
@security_guard('user_delete', require_ui=True)
def admin_delete_user(user_id):
    # Implementation ensures no automated deletion
```

### 2. Password Reset Safety  
```python
# CRITICAL RULE: Password resets must be explicitly requested
# NO automated password resets in production unless explicitly triggered
@production_safe('password_reset')
def reset_passwords():
    # Only triggered via admin UI or explicit user request
```

### 3. Production Safety Guards
All critical operations MUST use the `@security_guard` decorator:
- User deletion: `@security_guard('user_delete', require_ui=True)`
- Password resets: `@security_guard('password_reset', require_ui=True)`
- Bulk operations: `@security_guard('bulk_operation', require_ui=True)`

## 📁 Codebase Organization Standards

### Root Directory Rules
**ONLY these types of files belong in root:**
- Core application files (`app.py`, `security_guard.py`, etc.)
- Production configuration (`config.py`, `.env`, `production_config.py`)
- Critical deployment scripts (`deploy_azure_secure.ps1/.sh`)
- Essential documentation (`README.md`, security docs)
- Database and static assets

### Directory Structure
```
/                           # Production-ready files only
├── tests/                  # All test files and validation scripts
├── scripts/                # Utility scripts, migrations, setup tools
├── docs/                   # Documentation and reports
├── archived/               # Obsolete/alternative implementations
├── admin/                  # Admin blueprint module
├── auth/                   # Authentication blueprint module
├── dashboard/              # Dashboard blueprint module
├── learnings/              # Learning entries blueprint module
├── static/                 # CSS, JS, images
└── templates/              # Jinja2 templates
```

## 🧹 File Naming Conventions

### Test Files
- `test_*.py` - Unit tests
- `*_test.py` - Integration tests  
- `check_*.py` - Validation scripts
- `*_validation.py` - Validation scripts

### Script Files
- `setup_*.py` - Setup/installation scripts
- `migrate_*.py` - Database migration scripts
- `fix_*.py` - Bug fix scripts
- `reset_*.py` - Reset/cleanup scripts
- `debug_*.py` - Debugging utilities

### Documentation Files
- `*.md` - Markdown documentation
- `*_REPORT.md` - Implementation reports
- `*_GUIDE.md` - User guides
- `*_DOCS.md` - Technical documentation

## 🔧 Code Quality Standards

### 1. Security Decorators
```python
# ALWAYS use for sensitive operations
@require_admin
@security_guard('operation_name', require_ui=True)
def sensitive_operation():
    pass
```

### 2. Error Handling
```python
# ALWAYS wrap database operations
try:
    conn = get_db_connection()
    # database operations
    conn.commit()
except Exception as e:
    conn.rollback()
    flash(f'Error: {str(e)}', 'error')
finally:
    conn.close()
```

### 3. Input Validation
```python
# ALWAYS validate user inputs
if not username or len(username.strip()) == 0:
    flash('Username is required', 'error')
    return redirect(url_for('current_route'))
```

### 4. Logging for Audit Trail
```python
# Log all admin actions
log_admin_action('action_type', f'Description', 
                admin_user_id, request.remote_addr)
```

## 📊 Database Best Practices

### 1. Connection Management
```python
def get_db_connection():
    # Use consistent connection pattern
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

# ALWAYS close connections
conn = get_db_connection()
try:
    # operations
finally:
    conn.close()
```

### 2. SQL Injection Prevention
```python
# NEVER use string concatenation
# BAD: f"SELECT * FROM users WHERE id = {user_id}"
# GOOD: 
conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
```

### 3. Foreign Key Constraints
```sql
-- Ensure data integrity
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

## 🚀 Deployment Safety

### 1. Environment Variables
```bash
# Production environment MUST have:
FLASK_ENV=production
ADMIN_PASSWORD=secure_password
DEMO_PASSWORD=secure_password
FLASK_SECRET_KEY=cryptographically_secure_key
```

### 2. Pre-deployment Checklist
- [ ] All tests pass: `python -m pytest tests/`
- [ ] Security audit passes: `python azure_deployment_security_audit.py`
- [ ] Health check validates: `python production_health_check.py`
- [ ] Environment variables set in Azure portal
- [ ] Database backups created

### 3. Production Monitoring
```python
# Health check endpoints
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

## 🔍 Troubleshooting Guide

### Common Issues

#### 1. User Accidentally Deleted
```python
# Prevention: Security guards prevent this
# Recovery: Restore from database backup
# Check logs: grep "user_delete" app.log
```

#### 2. Password Reset Not Working
```python
# Check: Environment variables set correctly
# Check: production_config.py settings
# Verify: @security_guard decorators present
```

#### 3. Flask App Won't Start
```python
# Check: Import conflicts in __init__.py files
# Check: Decorator naming conflicts
# Verify: All required files in root directory
```

## 📋 Maintenance Tasks

### Weekly
- Review application logs for errors
- Check database integrity
- Verify backup systems working
- Monitor user activity patterns

### Monthly  
- Update dependencies: `pip list --outdated`
- Review security audit reports
- Clean up old log files
- Performance monitoring review

### Before Major Updates
- Full database backup
- Complete test suite run
- Security audit execution
- Staging deployment test

## 🛡️ Security Incident Response

### If Unauthorized User Deletion Detected
1. **IMMEDIATE**: Stop all automated processes
2. **ASSESS**: Check logs for scope of deletion
3. **RESTORE**: Restore from latest backup
4. **INVESTIGATE**: Review security guard logs
5. **DOCUMENT**: Create incident report
6. **PREVENT**: Add additional safeguards

### If Password Reset Abuse Detected  
1. **IMMEDIATE**: Disable password reset functionality
2. **NOTIFY**: Inform affected users
3. **AUDIT**: Review all recent password changes
4. **SECURE**: Force re-authentication for all users
5. **IMPROVE**: Enhance rate limiting and validation

## 💡 Best Practices Reminders

1. **Think Security First**: Every operation should consider security implications
2. **Log Everything**: Comprehensive logging enables debugging and auditing
3. **Test Thoroughly**: All critical paths should have automated tests
4. **Document Changes**: All modifications should be documented
5. **Review Regularly**: Code reviews should focus on security and maintainability
6. **Keep it Simple**: Complex code is harder to secure and maintain
7. **Environment Separation**: Development and production must be clearly separated
8. **Backup Strategy**: Regular backups are essential for data protection
9. **Monitor Production**: Continuous monitoring prevents issues becoming critical
10. **Stay Updated**: Regular updates for security patches and bug fixes

---

**Remember**: When in doubt about any operation's safety, err on the side of caution and ask for explicit confirmation before proceeding.
