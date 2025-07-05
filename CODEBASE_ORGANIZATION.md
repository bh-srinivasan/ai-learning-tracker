# Codebase Organization Summary

## 📁 Directory Structure

### `/` (Root) - Production Files Only
Contains only files required for production deployment:
- Core application files (app.py, security_guard.py, etc.)
- Configuration files (.env, config.py, etc.)
- Database and static assets
- Critical deployment scripts
- Essential documentation

### `/tests/` - Test Files
All test scripts, validation scripts, and testing utilities.

### `/scripts/` - Utility Scripts  
Setup scripts, database utilities, migration tools, and maintenance scripts.

### `/docs/` - Documentation
Non-critical documentation, reports, and reference materials.

### `/archived/` - Archived Files
Alternative implementations, obsolete files, and files of uncertain purpose.

## 🔒 Critical Business Rules Preserved

All files containing the following critical patterns have been preserved in root:
- NEVER DELETE USERS (security rule)
- @security_guard (security decorators)
- @production_safe (production safety)
- protected_users (user protection logic)
- admin_delete_user (admin functions)
- password_reset (password management)

## ⚠️ Safety Guarantees

✅ NO files deleted - only moved/organized
✅ ALL critical business logic preserved in root
✅ ALL security constraints maintained
✅ Production deployment unchanged
✅ All original files recoverable from organized folders

