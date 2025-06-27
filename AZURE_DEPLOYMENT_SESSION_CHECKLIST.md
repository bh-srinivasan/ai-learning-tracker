# Azure Deployment Checklist - AI Learning Tracker with Session Management

## Pre-deployment Checklist

### 1. Environment Variables
Set these in Azure App Service Configuration:
```bash
SECRET_KEY=<generate-strong-32-byte-key>
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
```

### 2. Dependencies Check
Ensure `requirements.txt` includes:
```
Flask>=2.3.0
Werkzeug>=2.3.0
gunicorn>=20.1.0
```

### 3. Database Migration
The app will automatically:
- Create new session management tables
- Add columns to existing tables
- Preserve existing user data

## Deployment Commands

### 1. Prepare for Deployment
```bash
# Ensure you're in the project directory
cd "AI_Learning"

# Commit latest changes
git add .
git commit -m "Session management implementation complete"
```

### 2. Deploy to Azure
```bash
# Deploy to Azure App Service
git push azure main

# Set environment variables
az webapp config appsettings set --resource-group ai-learning-rg --name ai-learning-app --settings SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
az webapp config appsettings set --resource-group ai-learning-rg --name ai-learning-app --settings FLASK_ENV="production"

# Restart the app
az webapp restart --resource-group ai-learning-rg --name ai-learning-app
```

### 3. Verify Deployment
```bash
# Check logs
az webapp log tail --resource-group ai-learning-rg --name ai-learning-app

# Test the application
curl -I https://ai-learning-app.azurewebsites.net
```

## Post-deployment Verification

### 1. Test Session Management
- [ ] Login functionality works
- [ ] Sessions persist across requests
- [ ] Session expiration warnings appear
- [ ] Admin session monitoring accessible
- [ ] Activity logging working

### 2. Security Verification
- [ ] HTTPS enforced
- [ ] Secure cookies set
- [ ] Session tokens are secure
- [ ] IP change detection works
- [ ] Failed login attempts logged

### 3. Admin Features
- [ ] Access admin panel at `/admin`
- [ ] Session monitoring at `/admin/sessions`
- [ ] User management working
- [ ] Course management functional
- [ ] Activity statistics displaying

### 4. Performance Check
- [ ] App responds within 3 seconds
- [ ] Session cleanup running
- [ ] Database queries optimized
- [ ] Static files served correctly

## Monitoring and Maintenance

### 1. Regular Checks
```bash
# Check application health
az webapp show --resource-group ai-learning-rg --name ai-learning-app --query "state"

# Monitor session activity
# Access admin panel for session statistics

# Check disk usage
az webapp show --resource-group ai-learning-rg --name ai-learning-app --query "siteConfig.diskQuotaInMb"
```

### 2. Session Data Cleanup
The app automatically cleans up expired sessions, but for manual cleanup:
```sql
-- Connect to database and run if needed
DELETE FROM user_sessions WHERE expires_at < datetime('now') AND is_active = 0;
DELETE FROM session_activity WHERE timestamp < datetime('now', '-30 days');
```

### 3. Security Monitoring
- Monitor session activity logs through admin panel
- Check for unusual IP changes or failed logins
- Review user activity patterns
- Monitor session duration and cleanup

## Troubleshooting

### Common Issues

#### 1. Session Not Persisting
```bash
# Check secret key is set
az webapp config appsettings list --resource-group ai-learning-rg --name ai-learning-app | grep SECRET_KEY

# Verify secure cookies setting
az webapp config appsettings list --resource-group ai-learning-rg --name ai-learning-app | grep FLASK_ENV
```

#### 2. Database Connection Issues
```bash
# Check app logs
az webapp log tail --resource-group ai-learning-rg --name ai-learning-app

# Restart the app
az webapp restart --resource-group ai-learning-rg --name ai-learning-app
```

#### 3. Session Cleanup Not Working
- Check background thread is running
- Verify database write permissions
- Monitor session activity table growth

## Scaling Considerations

### For High Traffic
1. Consider Redis for session storage:
   ```python
   # In production, consider:
   from flask_session import Session
   import redis
   
   app.config['SESSION_TYPE'] = 'redis'
   app.config['SESSION_REDIS'] = redis.from_url('redis://...')
   ```

2. Database optimization:
   ```sql
   CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
   CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
   CREATE INDEX idx_session_activity_timestamp ON session_activity(timestamp);
   ```

3. Load balancing considerations:
   - Sticky sessions or shared session storage
   - Database connection pooling
   - Static file CDN

## Security Hardening

### Production Security
1. **HTTPS Only**: Ensure SSL certificate is properly configured
2. **Security Headers**: Add security headers via web.config or app code
3. **Rate Limiting**: Consider implementing rate limiting for login attempts
4. **Monitoring**: Set up alerts for suspicious activity

### Environment Variables
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Set in Azure
az webapp config appsettings set --resource-group ai-learning-rg --name ai-learning-app --settings SECRET_KEY="your-generated-key"
```

## Success Criteria
- [ ] Application loads successfully
- [ ] User authentication works
- [ ] Sessions persist correctly
- [ ] Admin panel accessible
- [ ] Session monitoring functional
- [ ] Security features active
- [ ] Performance acceptable
- [ ] Logs show no errors

## Emergency Procedures

### If Sessions Fail
1. Clear all sessions:
   ```sql
   UPDATE user_sessions SET is_active = 0;
   ```

2. Force all users to re-login

3. Check secret key and restart app

### If Database Issues
1. Restart app service
2. Check database file permissions
3. Verify SQLite file exists and is writable

The AI Learning Tracker is now ready for production deployment with enterprise-grade session management!
