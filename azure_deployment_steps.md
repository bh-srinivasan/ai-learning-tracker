# Azure App Service Deployment Guide

## Step-by-Step Deployment

### 1. Login to Azure
```bash
az login
```

### 2. Create Resource Group
```bash
az group create --name ai-learning-rg --location "East US"
```

### 3. Create App Service Plan (Free Tier)
```bash
az appservice plan create \
  --name ai-learning-plan \
  --resource-group ai-learning-rg \
  --sku F1 \
  --is-linux
```

### 4. Create Web App
```bash
az webapp create \
  --resource-group ai-learning-rg \
  --plan ai-learning-plan \
  --name ai-learning-tracker-bharath \
  --runtime "PYTHON|3.9"
```

### 5. Configure App Settings
```bash
# Set Python version and startup command
az webapp config set \
  --resource-group ai-learning-rg \
  --name ai-learning-tracker-bharath \
  --startup-file "startup.py"

# Set environment variables
az webapp config appsettings set \
  --resource-group ai-learning-rg \
  --name ai-learning-tracker-bharath \
  --settings FLASK_ENV=production FLASK_APP=app.py
```

### 6. Deploy via Local Git
```bash
# Get deployment credentials
az webapp deployment user set --user-name bharath-deploy --password YourStrongPassword123!

# Configure local git deployment
az webapp deployment source config-local-git \
  --name ai-learning-tracker-bharath \
  --resource-group ai-learning-rg \
  --query url --output tsv
```

### 7. Deploy Your Code
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial deployment to Azure"

# Add Azure remote
git remote add azure https://bharath-deploy@ai-learning-tracker-bharath.scm.azurewebsites.net/ai-learning-tracker-bharath.git

# Deploy
git push azure main
```

### 8. Access Your App
Your app will be available at: 
**https://ai-learning-tracker-bharath.azurewebsites.net**

## Alternative: Quick Deploy Method

```bash
# One-command deployment (recommended for testing)
az webapp up \
  --name ai-learning-tracker-bharath \
  --resource-group ai-learning-rg \
  --plan ai-learning-plan \
  --sku F1 \
  --runtime "PYTHON:3.9" \
  --location "East US"
```

## Troubleshooting

### Common Issues:
1. **App sleeps after 20 minutes**: Normal for F1 tier
2. **Cold start delays**: First request after sleep takes longer
3. **Storage limitations**: SQLite file size limited to 1GB
4. **Memory limits**: 1GB RAM shared across all processes

### Solutions:
- Upgrade to B1 Basic tier for Always On feature
- Use Azure SQL Database for better performance
- Optimize your Flask app for memory usage

## Monitoring & Logs

```bash
# View logs
az webapp log tail --name ai-learning-tracker-bharath --resource-group ai-learning-rg

# Enable logging
az webapp log config --name ai-learning-tracker-bharath --resource-group ai-learning-rg --application-logging true --level information
```
