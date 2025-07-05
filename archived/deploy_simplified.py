#!/usr/bin/env python3
"""
Simple deployment script to push changes to Azure
"""

import subprocess
import sys

def run_command(command, description):
    """Run a shell command and print the result"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Command: {command}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception running command: {e}")
        return False

def main():
    """Main deployment function"""
    print("Starting Azure deployment...")
    
    # Add files to git
    if not run_command("git add .", "Adding files to git"):
        print("Failed to add files to git")
        return False
    
    # Commit changes
    if not run_command('git commit -m "Restore to working version - simplified app without complex imports"', "Committing changes"):
        print("Commit may have failed or no changes to commit")
    
    # Push to Azure
    if not run_command("git push azure master", "Pushing to Azure"):
        print("Failed to push to Azure")
        return False
    
    print("\n=== Deployment completed successfully! ===")
    print("Check https://ai-learning-tracker.azurewebsites.net in a few minutes")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
