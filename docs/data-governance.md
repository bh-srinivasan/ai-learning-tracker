# Data Governance and Backup Policies

## 🔐 Data Integrity Rules

### CRITICAL PRINCIPLES
1. **NEVER copy local/test data to production**
2. **NEVER overwrite production data without verified backup**
3. **ALWAYS investigate Azure backup history before production changes**
4. **ALWAYS verify production data is restored from production backups only**

### Environment Separation
- **Development**: Local SQLite database, test users only
- **Staging**: Replica of production structure with test data
- **Production**: Real user data, Azure-hosted, backup-protected

### Data Movement Restrictions
- ❌ **PROHIBITED**: Local → Production
- ❌ **PROHIBITED**: Test → Production  
- ❌ **PROHIBITED**: Any unverified source → Production
- ✅ **ALLOWED**: Production Backup → Production
- ✅ **ALLOWED**: Verified Migration Script → Production

## 🛡️ Protection Mechanisms

### Automated Safeguards
1. **Environment Detection**: Automatically detect production vs development
2. **Data Validation**: Check database content for test vs production indicators
3. **Backup Verification**: Require recent backups before any production changes
4. **Audit Logging**: Log all data operations with timestamps and sources

### Manual Checkpoints
1. **Confirmation Steps**: Require explicit confirmation for destructive operations
2. **Peer Review**: Require second person approval for production data changes
3. **Documentation**: Document all production data operations

## 📋 Azure Backup Configuration

### Automated Backups
- **Frequency**: Daily at 2 AM UTC
- **Retention**: 30 days
- **Storage**: Azure Blob Storage with redundancy
- **Verification**: Weekly backup integrity checks

### Manual Backup Requirements
- **Before Deployments**: Create backup before any production deployment
- **Before Migrations**: Create backup before database schema changes
- **Before Maintenance**: Create backup before any system maintenance

### Recovery Procedures
1. **Immediate Recovery**: Restore from most recent backup
2. **Point-in-Time Recovery**: Restore from specific backup date
3. **Partial Recovery**: Restore specific tables or data sets
4. **Disaster Recovery**: Full system restoration from backup

## 🚨 Incident Response

### Data Breach Response
1. **STOP**: Immediately halt all operations
2. **ASSESS**: Determine scope and impact of breach
3. **ISOLATE**: Prevent further damage
4. **RECOVER**: Restore from verified backups
5. **INVESTIGATE**: Determine root cause
6. **PREVENT**: Implement additional safeguards

### Emergency Contacts
- **Azure Support**: Critical/A severity ticket
- **Database Administrator**: [Contact Info]
- **Security Team**: [Contact Info]
- **Management**: [Contact Info]

## ✅ Compliance Checklist

### Before Any Production Operation
- [ ] Environment verified as correct
- [ ] Recent backup confirmed available
- [ ] Data source verified as production-appropriate
- [ ] Approval obtained from authorized personnel
- [ ] Rollback plan documented
- [ ] Post-operation verification plan prepared

### After Any Production Operation
- [ ] Operation success verified
- [ ] Data integrity confirmed
- [ ] New backup created
- [ ] Operation documented
- [ ] Stakeholders notified
- [ ] Monitoring alerts reviewed

---

**Document Version**: 1.0  
**Last Updated**: {datetime.now().isoformat()}  
**Next Review**: {(datetime.now() + timedelta(days=90)).isoformat()}  
**Owner**: Data Governance Team
