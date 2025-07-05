# Azure Deployment Configuration for AI Learning Tracker

## Environment Variables Required for Azure

### Application Configuration
```bash
FLASK_ENV=production
NODE_ENV=production
FLASK_SECRET_KEY=your-production-secret-key-here
DATABASE_URL=sqlite:///ai_learning.db
```

### User Credentials (Environment-Based)
```bash
ADMIN_PASSWORD=YourSecureAdminPassword123!
DEMO_USERNAME=demo
DEMO_PASSWORD=DemoUserPassword123!
```

### Security Settings
```bash
SESSION_TIMEOUT=3600
PASSWORD_MIN_LENGTH=12
MAX_LOGIN_ATTEMPTS=5
```

### Production Safety Settings
```bash
ALLOW_BULK_OPERATIONS=false
REQUIRE_UI_FOR_SENSITIVE_OPS=true
ENABLE_PASSWORD_RESET_API=false
ALLOW_USER_REGISTRATION=false
```

## Azure App Service Configuration

### Application Settings
Add these in Azure Portal → App Service → Configuration → Application Settings:

| Setting Name | Value | Description |
|--------------|-------|-------------|
| `FLASK_ENV` | `production` | Sets Flask to production mode |
| `NODE_ENV` | `production` | Sets Node.js environment |
| `FLASK_SECRET_KEY` | `[generated-secret]` | Flask session encryption key |
| `ADMIN_PASSWORD` | `[secure-password]` | Admin user password |
| `DEMO_PASSWORD` | `[secure-password]` | Demo user password |
| `SESSION_TIMEOUT` | `3600` | Session timeout in seconds |
| `PASSWORD_MIN_LENGTH` | `12` | Minimum password length |
| `MAX_LOGIN_ATTEMPTS` | `5` | Maximum login attempts |

### Startup Command
```bash
python app.py
```

## Production Safety Features

### 1. UI-Only Sensitive Operations
In production, these operations can ONLY be performed through the web interface:
- Password resets (individual and bulk)
- User deletion
- Database cleanup
- Administrative overrides

### 2. Backend Script Protection
All backend scripts require explicit user authorization:
```python
# This will be BLOCKED in production
reset_user_password('admin', 'new_password')

# This will be ALLOWED (with explicit authorization)
reset_user_password('admin', 'new_password', explicit_user_request=True)
```

### 3. Environment-Based Restrictions
Production environment automatically enforces:
- No bulk operations without UI
- Stronger password requirements (12+ characters)
- Limited login attempts (5 max)
- HTTPS-only cookies
- CSRF protection enabled
- Audit logging for all operations

### 4. User Management Safeguards
- Admin can reset ANY user's password via UI
- All password resets are logged with full audit trail
- No hardcoded credentials in production
- Environment variables used for all sensitive data

## Deployment Checklist

### Pre-Deployment
- [ ] Run security audit: `python azure_deployment_security_audit.py`
- [ ] Run all tests: `python test_controlled_password_reset.py`
- [ ] Verify environment variables are set
- [ ] Review audit logs for any hardcoded credentials
- [ ] Confirm all user operations are UI-protected

### Deployment Steps
1. **Set Environment Variables** in Azure App Service
2. **Deploy Code** using Azure DevOps or GitHub Actions
3. **Verify Database** is accessible and initialized
4. **Test Admin Login** with environment-based credentials
5. **Verify UI Operations** work correctly
6. **Confirm Backend Protection** blocks unauthorized operations

### Post-Deployment Verification
- [ ] Admin can log in with environment password
- [ ] Demo user can log in with environment password
- [ ] Password reset works through UI
- [ ] Backend scripts are blocked without explicit authorization
- [ ] All operations are properly logged
- [ ] No users can be deleted accidentally

## Security Architecture

### Production Operation Flow
```
User Action (UI) → Admin Authentication → Security Guard Validation → Operation Execution → Audit Logging
                     ↓
Backend Script → Explicit Authorization Check → Security Guard Validation → Operation Execution → Audit Logging
                     ↓
Automated Process → BLOCKED (No explicit authorization)
```

### Security Layers
1. **Environment Detection**: Automatic production vs development detection
2. **UI Authentication**: Admin must be logged in through web interface
3. **Security Guard Validation**: Operation-specific security checks
4. **Explicit Authorization**: Backend operations require user consent
5. **Audit Logging**: All operations logged for compliance

## Monitoring and Maintenance

### Application Insights
Configure Azure Application Insights to monitor:
- User login attempts and failures
- Password reset operations
- Security guard blocks
- Error rates and performance

### Log Analytics
Monitor these log patterns:
- `PRODUCTION SAFETY`: Operations blocked due to production restrictions
- `EXPLICIT AUTHORIZATION`: Backend operations with user consent
- `Security guard blocked operation`: Unauthorized operation attempts
- `Azure production operation`: All production operations

### Alerts
Set up alerts for:
- Failed login attempts > 10 per hour
- Security guard blocks > 5 per hour
- Backend password reset attempts
- Database connection failures

## Troubleshooting

### Common Issues
1. **Admin Can't Login**: Check `ADMIN_PASSWORD` environment variable
2. **Password Reset Blocked**: Ensure operation is UI-triggered
3. **Backend Script Fails**: Add `explicit_user_request=True` parameter
4. **Environment Detection Wrong**: Set `FLASK_ENV=production`

### Debug Commands
```bash
# Check environment detection
python -c "from production_config import ProductionConfig; print(f'Environment: {ProductionConfig.get_environment()}, Production: {ProductionConfig.is_production()}')"

# Validate environment variables
python -c "from production_config import ProductionConfig; missing = ProductionConfig.validate_environment_variables(); print('Missing variables:', missing)"

# Test security guard
python test_controlled_password_reset.py
```

## Best Practices

### 1. Never Hardcode Secrets
- Use Azure Key Vault for sensitive data
- Environment variables for all configuration
- No passwords in source code

### 2. Principle of Least Privilege
- UI operations for admins only
- Backend operations require explicit authorization
- Read-only operations don't require special permissions

### 3. Defense in Depth
- Multiple security layers (environment, authentication, authorization)
- Comprehensive audit logging
- Automatic detection of unsafe operations

### 4. Continuous Monitoring
- Regular security audits
- Automated testing of security controls
- Log analysis for unusual patterns

This configuration ensures secure, scalable deployment to Azure while maintaining full functionality for legitimate administrative operations.
