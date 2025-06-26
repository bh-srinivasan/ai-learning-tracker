# Deploy AI Learning Tracker to Azure App Service

## 🎯 Azure App Service Free Tier Limits

### **F1 (Free) Tier Specifications:**
- **Compute**: 1 GB RAM, Shared CPU
- **Storage**: 1 GB disk space
- **Bandwidth**: 165 MB/day (~ 5 GB/month)
- **Custom domains**: Not supported (uses *.azurewebsites.net)
- **SSL certificates**: Shared SSL only
- **Deployment slots**: Not available
- **Auto-scaling**: Not available
- **Always On**: Not available (app sleeps after 20 min inactivity)
- **Maximum apps**: 10 per subscription
- **Duration**: No time limit (permanent)

### **For Microsoft Employees:**
- You get **$150/month Azure credits** through Visual Studio Enterprise
- Additional credits through Microsoft 365 Developer Program
- Consider upgrading to **B1 Basic** ($13.14/month) for better performance

## Prerequisites
- Azure subscription (free with Microsoft employee benefits)
- Azure CLI installed ✅
- Git repository

## Step 1: Prepare for Deployment

### Create startup.py (required for Azure)
```python
from app import app

if __name__ == "__main__":
    app.run()
```

### Update requirements.txt
Make sure your requirements.txt includes:
```
Flask==2.3.3
Werkzeug==2.3.7
gunicorn==21.2.0
```

### Create .deployment file
```
[config]
command = deploy.cmd
```

### Create deploy.cmd
```cmd
@if "%SCM_TRACE_LEVEL%" NEQ "4" @echo off

:: ----------------------
:: KUDU Deployment Script
:: Version: 1.0.17
:: ----------------------

:: Prerequisites
:: -------------

:: Verify node.js installed
where node 2>nul >nul
IF %ERRORLEVEL% NEQ 0 (
  echo Missing node.js executable, please install node.js, if already installed make sure it can be reached from current environment.
  goto error
)

:: Setup
:: -----

setlocal enabledelayedexpansion

SET ARTIFACTS=%~dp0%..\artifacts

IF NOT DEFINED DEPLOYMENT_SOURCE (
  SET DEPLOYMENT_SOURCE=%~dp0%.
)

IF NOT DEFINED DEPLOYMENT_TARGET (
  SET DEPLOYMENT_TARGET=%ARTIFACTS%\wwwroot
)

IF NOT DEFINED NEXT_MANIFEST_PATH (
  SET NEXT_MANIFEST_PATH=%ARTIFACTS%\manifest

  IF NOT DEFINED PREVIOUS_MANIFEST_PATH (
    SET PREVIOUS_MANIFEST_PATH=%ARTIFACTS%\manifest
  )
)

IF NOT DEFINED KUDU_SYNC_CMD (
  :: Install kudu sync
  echo Installing Kudu Sync
  call npm install kudusync -g --silent
  IF !ERRORLEVEL! NEQ 0 goto error

  :: Locally just running "kuduSync" would also work
  SET KUDU_SYNC_CMD=%appdata%\npm\kuduSync.cmd
)

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Deployment
:: ----------

echo Handling python deployment.

:: 1. KuduSync
IF /I "%IN_PLACE_DEPLOYMENT%" NEQ "1" (
  call :ExecuteCmd "%KUDU_SYNC_CMD%" -v 50 -f "%DEPLOYMENT_SOURCE%" -t "%DEPLOYMENT_TARGET%" -n "%NEXT_MANIFEST_PATH%" -p "%PREVIOUS_MANIFEST_PATH%" -i ".git;.hg;.deployment;deploy.cmd"
  IF !ERRORLEVEL! NEQ 0 goto error
)

:: 2. Install packages
echo Pip install requirements.
D:\home\python364x64\python.exe -m pip install --upgrade pip
IF !ERRORLEVEL! NEQ 0 goto error

D:\home\python364x64\python.exe -m pip install -r requirements.txt
IF !ERRORLEVEL! NEQ 0 goto error

:: 3. Copy web.config
IF EXIST "%DEPLOYMENT_SOURCE%\web.config" (
  copy "%DEPLOYMENT_SOURCE%\web.config" "%DEPLOYMENT_TARGET%\web.config"
)

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto end

:: Execute command routine that will echo out when error
:ExecuteCmd
setlocal
set _CMD_=%*
call %_CMD_%
if "%ERRORLEVEL%" NEQ "0" echo Failed exitCode=%ERRORLEVEL%, command=%_CMD_%
exit /b %ERRORLEVEL%

:error
endlocal
echo An error has occurred during web site deployment.
call :exitSetErrorLevel
call :exitFromFunction 2>nul

:exitSetErrorLevel
exit /b 1

:exitFromFunction
()

:end
endlocal
echo Finished successfully.
```

## Step 2: Azure CLI Deployment Commands

```bash
# Login to Azure
az login

# Create resource group
az group create --name ai-learning-rg --location "East US"

# Create App Service plan (Free tier)
az appservice plan create --name ai-learning-plan --resource-group ai-learning-rg --sku F1 --is-linux

# Create web app
az webapp create --resource-group ai-learning-rg --plan ai-learning-plan --name ai-learning-tracker-[your-name] --runtime "PYTHON|3.9"

# Configure startup file
az webapp config set --resource-group ai-learning-rg --name ai-learning-tracker-[your-name] --startup-file "startup.py"

# Deploy from local git
az webapp deployment source config-local-git --name ai-learning-tracker-[your-name] --resource-group ai-learning-rg

# Get deployment URL
az webapp deployment list-publishing-credentials --name ai-learning-tracker-[your-name] --resource-group ai-learning-rg
```

## Step 3: Git Deployment

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Add Azure remote (replace with your URL from above command)
git remote add azure https://[deployment-username]@ai-learning-tracker-[your-name].scm.azurewebsites.net/ai-learning-tracker-[your-name].git

# Deploy
git push azure main
```

## Environment Variables in Azure
Set these in Azure Portal > App Service > Configuration:

- `FLASK_ENV=production`
- `FLASK_APP=app.py`
- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`

## Database Considerations
- SQLite works for development but consider Azure SQL Database for production
- For SQLite, the database file will be stored in the app's file system
