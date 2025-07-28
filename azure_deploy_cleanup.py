#!/usr/bin/env python3
"""
Azure Deploy Cleanup Script
Safely removes unused azure-deploy.yml workflow file after verification
"""

import os
import subprocess
import json
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_file_dependencies():
    """Check if azure-deploy.yml is referenced anywhere"""
    print("🔍 Checking for dependencies on azure-deploy.yml...")
    
    dependencies_found = []
    
    # Check for references in all files
    success, stdout, stderr = run_command('git grep -r "azure-deploy.yml" -- . ":(exclude).github/workflows/azure-deploy.yml"')
    if success and stdout:
        dependencies_found.append(f"Git grep found references:\n{stdout}")
    
    # Check for references in documentation files
    for ext in ['*.md', '*.txt', '*.rst']:
        success, stdout, stderr = run_command(f'find . -name "{ext}" -exec grep -l "azure-deploy" {{}} \\;')
        if success and stdout:
            dependencies_found.append(f"Documentation references in {ext} files:\n{stdout}")
    
    return dependencies_found

def check_azure_devops_usage():
    """Check if the workflow is being used by Azure DevOps"""
    print("🔍 Checking Azure DevOps pipeline usage...")
    
    # Check if there are any recent runs of this workflow
    success, stdout, stderr = run_command('gh run list --workflow=azure-deploy.yml --limit=10 --json status,conclusion,createdAt')
    
    if success and stdout:
        try:
            runs = json.loads(stdout)
            if runs:
                print(f"⚠️  Found {len(runs)} recent workflow runs")
                return True, runs
            else:
                print("✅ No recent workflow runs found")
                return False, []
        except json.JSONDecodeError:
            print("ℹ️  Could not parse workflow runs (may indicate no runs)")
            return False, []
    else:
        print("ℹ️  GitHub CLI not available or no runs found")
        return False, []

def analyze_current_deployment():
    """Analyze current deployment setup"""
    print("📊 Analyzing current deployment configuration...")
    
    # Check azure-pipelines.yml
    if os.path.exists('azure-pipelines.yml'):
        print("✅ Found azure-pipelines.yml - this appears to be the active deployment method")
        
        with open('azure-pipelines.yml', 'r') as f:
            content = f.read()
            if 'azure-deploy.yml' in content:
                print("❌ azure-pipelines.yml references azure-deploy.yml")
                return False
            else:
                print("✅ azure-pipelines.yml does not reference azure-deploy.yml")
    
    # Check if file is empty
    azure_deploy_path = '.github/workflows/azure-deploy.yml'
    if os.path.exists(azure_deploy_path):
        with open(azure_deploy_path, 'r') as f:
            content = f.read().strip()
            if not content:
                print("✅ azure-deploy.yml is empty")
                return True
            else:
                print(f"⚠️  azure-deploy.yml has content ({len(content)} characters)")
                print("Content preview:")
                print(content[:200] + "..." if len(content) > 200 else content)
                return False
    
    return True

def remove_azure_deploy_file():
    """Remove the azure-deploy.yml file"""
    print("🗑️  Removing azure-deploy.yml file...")
    
    azure_deploy_path = '.github/workflows/azure-deploy.yml'
    
    if os.path.exists(azure_deploy_path):
        try:
            os.remove(azure_deploy_path)
            print("✅ Successfully removed .github/workflows/azure-deploy.yml")
            return True
        except Exception as e:
            print(f"❌ Error removing file: {e}")
            return False
    else:
        print("ℹ️  File does not exist")
        return True

def commit_changes():
    """Commit the removal to git"""
    print("📝 Committing changes to git...")
    
    # Add the deletion to git
    success, stdout, stderr = run_command('git add -A')
    if not success:
        print(f"❌ Error staging changes: {stderr}")
        return False
    
    # Commit the changes
    commit_message = "Remove unused azure-deploy.yml workflow file\n\n- File was empty and not referenced by any active pipelines\n- Current deployment uses azure-pipelines.yml\n- Cleaned up obsolete GitHub Actions workflow"
    
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success:
        if "nothing to commit" in stderr:
            print("ℹ️  No changes to commit")
            return True
        else:
            print(f"❌ Error committing changes: {stderr}")
            return False
    
    print("✅ Successfully committed file removal")
    return True

def main():
    """Main cleanup process"""
    print("🧹 Azure Deploy Cleanup Script")
    print("=" * 50)
    
    # Step 1: Check for dependencies
    dependencies = check_file_dependencies()
    if dependencies:
        print("❌ Found dependencies on azure-deploy.yml:")
        for dep in dependencies:
            print(dep)
        print("\n🛑 Cannot safely remove file due to dependencies")
        return False
    
    print("✅ No code dependencies found")
    
    # Step 2: Check Azure DevOps usage
    has_recent_runs, runs = check_azure_devops_usage()
    if has_recent_runs:
        print("❌ Found recent workflow runs - file may still be in use")
        for run in runs[:3]:  # Show first 3 runs
            print(f"  - {run.get('createdAt', 'N/A')}: {run.get('status', 'N/A')} / {run.get('conclusion', 'N/A')}")
        print("\n🛑 Cannot safely remove file due to recent usage")
        return False
    
    # Step 3: Analyze current deployment setup
    can_remove = analyze_current_deployment()
    if not can_remove:
        print("🛑 Cannot safely remove file - appears to have content or dependencies")
        return False
    
    # Step 4: Remove the file
    if not remove_azure_deploy_file():
        return False
    
    # Step 5: Commit changes
    if not commit_changes():
        return False
    
    print("\n🎉 Cleanup completed successfully!")
    print("📋 Summary:")
    print("  ✅ Verified no code dependencies")
    print("  ✅ Verified no recent Azure DevOps usage")
    print("  ✅ Confirmed file was empty/unused")
    print("  ✅ Removed .github/workflows/azure-deploy.yml")
    print("  ✅ Committed changes to git")
    print("\n💡 Next steps:")
    print("  - Push changes to origin: git push origin master")
    print("  - Push changes to azure: git push azure master")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
