# Deploy to Render.com (Free & Easy)

## Why Render.com?
- ✅ No credit card required
- ✅ 750 hours/month free (enough for personal projects)
- ✅ Direct GitHub integration
- ✅ Automatic deployments
- ✅ No account/tenant complications

## Step 1: Prepare Your Repository

### Create requirements.txt (if not already done)
```
Flask==2.3.3
Werkzeug==2.3.7
gunicorn==21.2.0
```

### Create render.yaml
```yaml
services:
  - type: web
    name: ai-learning-tracker
    runtime: python3
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    plan: free
    envVars:
      - key: FLASK_ENV
        value: production
```

## Step 2: Deploy
1. Go to https://render.com
2. Sign up with GitHub
3. Connect your repository
4. Deploy automatically!

## Step 3: Access Your App
Your app will be available at: https://ai-learning-tracker-[random].onrender.com

## Advantages:
- Deploy in 5 minutes
- No Azure account issues
- Automatic HTTPS
- Free custom domain support
- Easy to use
