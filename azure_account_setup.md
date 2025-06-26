# Azure Account Configuration Guide

## 🎯 Check Which Azure Account You're Using

### Method 1: Azure Portal
1. Go to https://portal.azure.com
2. Look at top-right corner - shows current logged-in account
3. Click your profile → "Switch directory" to change tenants

### Method 2: Azure CLI (after installation)
```bash
# Check current account
az account show

# List all available accounts
az account list

# Check current subscription
az account list --query "[?isDefault]"
```

## 🔄 Switch to Different Azure Account

### Option A: Sign out and sign in with different account
```bash
# Sign out current account
az logout

# Sign in with your credits account
az login
```

### Option B: Add multiple accounts
```bash
# Add additional account without signing out
az login --tenant <your-credits-tenant-id>

# List all accounts
az account list --output table

# Set specific subscription as default
az account set --subscription "<subscription-name-or-id>"
```

## 🏢 Microsoft Employee Account Types

### 1. Corporate Account (@microsoft.com)
- **Tenant**: Microsoft Corporation
- **Use for**: Work-related resources
- **Credits**: Usually limited or none

### 2. Personal Account with Visual Studio Benefits
- **Tenant**: Default Directory
- **Use for**: Personal development, learning
- **Credits**: $150/month with Visual Studio Enterprise
- **Credits**: $50/month with Visual Studio Professional

### 3. Microsoft 365 Developer Account
- **Tenant**: Custom developer tenant
- **Use for**: Development and testing
- **Credits**: Additional free credits

## 🎯 Finding Your Credits Account

### Check Visual Studio Subscriptions:
1. Go to https://my.visualstudio.com
2. Sign in with your Microsoft account
3. Look for "Azure" benefits
4. Note the subscription ID and email

### Check Azure Subscriptions:
1. Go to https://portal.azure.com
2. Navigate to "Subscriptions"
3. Look for subscriptions with credits
4. Note the Directory/Tenant information

## 🚀 Recommended Setup for Deployment

### Step 1: Identify Your Credits Account
```bash
# After Azure CLI installation, try logging in
az login

# This will open browser - sign in with your CREDITS account
# (not your corporate @microsoft.com account)

# Verify you're using the right account
az account show --query "{Name:name, Id:id, TenantId:tenantId, User:user.name}"
```

### Step 2: Create Resource Group with Credits Account
```bash
# Create resource group in your credits subscription
az group create --name ai-learning-rg --location "East US"

# Verify it's created in the right subscription
az group show --name ai-learning-rg --query "{Name:name, SubscriptionId:id}"
```

## 🛠️ Alternative: Use Azure Portal for Initial Setup

If Azure CLI is problematic, you can set everything up via portal:

1. **Go to Azure Portal** with your credits account
2. **Create Resource Group**: 
   - Name: `ai-learning-rg`
   - Region: `East US`
3. **Create App Service Plan**:
   - Name: `ai-learning-plan`
   - OS: `Linux`
   - Pricing: `F1 (Free)`
4. **Create Web App**:
   - Name: `ai-learning-tracker-bharath`
   - Runtime: `Python 3.9`
   - App Service Plan: Use the one created above

## 🔍 Troubleshooting Account Issues

### Problem: "Subscription not found"
**Solution**: You're logged into wrong account
```bash
az logout
az login  # Sign in with credits account
```

### Problem: "No subscriptions found"
**Solution**: Account might not have Azure access
1. Check https://my.visualstudio.com for Azure benefits
2. Activate Azure subscription if needed
3. Contact IT if corporate account restrictions

### Problem: "Insufficient permissions"
**Solution**: Wrong tenant or role
```bash
# Check current tenant
az account tenant list

# Switch to correct tenant
az login --tenant <tenant-id>
```

## 💡 Pro Tips for Microsoft Employees

1. **Use Personal Microsoft Account** for Azure credits (not @microsoft.com)
2. **Visual Studio Enterprise** gives $150/month
3. **Visual Studio Professional** gives $50/month  
4. **Avoid using corporate account** for personal projects
5. **Check MyBenefits portal** for additional credits
