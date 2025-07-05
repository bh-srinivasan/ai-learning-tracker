# Git and Azure Deployment Guide

## 🔧 Pre-Deployment Checklist

### Files to Commit
✅ Application code changes
✅ Database schema updates  
✅ Configuration files (excluding .env)
✅ Documentation updates

### Files to Exclude
❌ .env (sensitive environment variables)
❌ *.db files (database should be managed separately)
❌ Test/debug scripts
❌ Temporary files

## 🚀 Deployment Process

### Step 1: Prepare Environment Variables for Azure
Before deploying, set up environment variables in Azure App Service:

1. Go to Azure Portal
2. Navigate to your App Service: ai-learning-tracker-bharath
3. Go to Configuration > Application settings
4. Add the following environment variables:

```
ADMIN_PASSWORD=YourSecureAdminPassword123!
DEMO_USERNAME=demo
DEMO_PASSWORD=DemoUserPassword123!
FLASK_SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_TIMEOUT=3600
PASSWORD_MIN_LENGTH=8
```

### Step 2: Git Commit and Push

```bash
# Add important files only
git add admin/routes.py
git add app.py
git add requirements.txt
git add config.py
git add .gitignore
git add web.config

# Commit changes
git commit -m "Fix LinkedIn course addition and global learnings count

- Added missing url, category, difficulty columns to courses table
- Fixed LinkedIn course insertion logic
- Updated admin learning entries to be properly marked as global
- Added environment variable configuration
- Enhanced security with .env file setup
- Updated requirements.txt with python-dotenv"

# Push to Azure
git push azure master
```

### Step 3: Database Migration on Azure
Since database changes were made locally, you'll need to handle this on Azure:

Options:
1. Let the app recreate the database (if data loss is acceptable)
2. Run migration scripts on Azure
3. Upload updated database file

### Step 4: Verify Deployment
1. Check Azure deployment logs
2. Test LinkedIn course addition functionality
3. Verify global learnings count
4. Test login with environment variable passwords

## 🔒 Security Notes
- Never commit .env files
- Set environment variables in Azure App Service Configuration
- Use strong passwords in production
- Monitor deployment logs for any issues
