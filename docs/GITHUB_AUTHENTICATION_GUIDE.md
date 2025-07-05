# GitHub Authentication Setup Guide

## Authentication Failed - Setup Required

The GitHub push failed because authentication is required. Here are your options:

## Option 1: Personal Access Token (Recommended)

1. **Create a Personal Access Token**:
   - Go to GitHub: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a name like "AI Learning Tracker"
   - Select scopes: Check "repo" (gives full repository access)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again)

2. **Use the token for authentication**:
   ```bash
   git push -u origin master
   ```
   - Username: `bh-srinivasan`
   - Password: `your-personal-access-token` (paste the token here)

## Option 2: GitHub CLI (Alternative)

1. **Install GitHub CLI**: 
   - Download from: https://cli.github.com/
   - Or use: `winget install --id GitHub.cli`

2. **Authenticate**:
   ```bash
   gh auth login
   ```
   - Follow the prompts to authenticate

3. **Push using GitHub CLI**:
   ```bash
   gh repo sync
   ```

## Option 3: SSH Key (For Future Use)

If you want to avoid passwords in the future:

1. **Generate SSH key**:
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com"
   ```

2. **Add to GitHub**:
   - Copy the public key: `cat ~/.ssh/id_ed25519.pub`
   - Go to GitHub Settings → SSH and GPG keys
   - Add the key

3. **Change remote to SSH**:
   ```bash
   git remote set-url origin git@github.com:bh-srinivasan/ai-learning-tracker.git
   ```

## Quick Fix: Use Personal Access Token

The fastest solution is Option 1. After you get your token:

```bash
git push -u origin master
```

When prompted:
- Username: `bh-srinivasan`
- Password: `your-personal-access-token`

## After Successful Push

Once authentication works, you'll see:
- Your code will be uploaded to GitHub
- Repository will be publicly accessible (if you made it public)
- You can use the deployment script for future updates

## Repository URL

Your GitHub repository will be available at:
https://github.com/bh-srinivasan/ai-learning-tracker

## Need Help?

If you encounter issues:
1. Make sure the repository exists and is accessible
2. Check that your username is correct: `bh-srinivasan`
3. Ensure your Personal Access Token has the right permissions
4. Try the GitHub CLI method if token authentication doesn't work
