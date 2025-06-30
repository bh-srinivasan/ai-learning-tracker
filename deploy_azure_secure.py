#!/usr/bin/env python3
"""
Azure Deployment Script for AI Learning Tracker
Handles git commits, Azure deployment, security checks, and logging.

Features:
- Git status and commit management
- Azure deployment with environment variables
- Security scanning for hardcoded password resets
- Comprehensive logging
- Modular and reusable functions
"""

import os
import sys
import subprocess
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configure logging
LOG_FILE = "deployment_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentManager:
    """Main deployment manager class"""
    
    def __init__(self):
        self.repo_path = Path.cwd()
        self.protected_users = ['admin', 'bharath']
        self.azure_app_name = "ai-learning-tracker-bharath"
        
    def run_command(self, cmd: str, capture_output: bool = True) -> Tuple[bool, str]:
        """Run a shell command and return success status and output"""
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, cwd=self.repo_path
                )
                return result.returncode == 0, result.stdout.strip()
            else:
                result = subprocess.run(cmd, shell=True, cwd=self.repo_path)
                return result.returncode == 0, ""
        except Exception as e:
            logger.error(f"Error running command '{cmd}': {e}")
            return False, str(e)

    def check_git_status(self) -> Dict[str, any]:
        """Check git status for uncommitted changes"""
        logger.info("[GIT] Checking git status...")
        
        success, output = self.run_command("git status --porcelain")
        if not success:
            logger.error("Failed to check git status")
            return {"has_changes": True, "error": "Failed to check git status"}
        
        has_uncommitted = bool(output.strip())
        
        if has_uncommitted:
            logger.warning("[WARNING] Uncommitted changes detected:")
            lines = output.strip().split('\n')
            for line in lines:
                logger.warning(f"    {line}")
            return {"has_changes": True, "files": lines}
        else:
            logger.info("[SUCCESS] No uncommitted changes")
            return {"has_changes": False}

    def commit_changes(self, message: str) -> bool:
        """Commit current changes with the given message"""
        logger.info(f"[COMMIT] Committing changes: {message}")
        
        # Add all changes
        success, _ = self.run_command("git add -A")
        if not success:
            logger.error("Failed to stage changes")
            return False
        
        # Commit changes
        success, _ = self.run_command(f'git commit -m "{message}"')
        if success:
            logger.info("[SUCCESS] Changes committed successfully")
            return True
        else:
            logger.error("[ERROR] Failed to commit changes")
            return False

    def scan_hardcoded_password_resets(self) -> List[Dict[str, any]]:
        """Scan codebase for hardcoded password reset logic for protected users"""
        logger.info("[SECURITY] Scanning for hardcoded password reset logic...")
        
        issues = []
        
        # Patterns to look for - only admin-related patterns now matter
        patterns = [
            (r"generate_password_hash\s*\(\s*['\"]admin['\"]", "Hardcoded admin password generation"),
            (r"admin['\"]\s*,\s*['\"](admin|password)", "Hardcoded admin credentials"),
            (r"UPDATE\s+users\s+SET\s+password_hash.*admin", "Direct password update for admin"),
            (r"INSERT.*admin.*password", "Hardcoded admin user creation"),
        ]
        
        # Files to scan
        python_files = list(self.repo_path.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, description in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            "file": str(file_path.relative_to(self.repo_path)),
                            "line": line_num,
                            "pattern": description,
                            "match": match.group(),
                            "severity": "HIGH" if "admin" in match.group().lower() else "MEDIUM"
                        })
                        
            except Exception as e:
                logger.warning(f"Could not scan {file_path}: {e}")
        
        if issues:
            logger.warning(f"⚠️  Found {len(issues)} potential security issues:")
            for issue in issues:
                logger.warning(f"    {issue['file']}:{issue['line']} - {issue['pattern']}")
                logger.warning(f"        Match: {issue['match']}")
        else:
            logger.info("✅ No hardcoded password reset issues found")
            
        return issues

    def check_protected_user_logic(self) -> bool:
        """Verify that protected user logic is in place"""
        logger.info("🛡️  Checking protected user logic...")
        
        app_py = self.repo_path / "app.py"
        if not app_py.exists():
            logger.error("app.py not found")
            return False
            
        try:
            with open(app_py, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for protected user arrays/lists
            protected_patterns = [
                r"protected_users\s*=\s*\[.*bharath",
                r"PROTECTED_USERS\s*=\s*\[.*bharath",
                r"if.*username.*in.*protected",
                r"if.*bharath.*protected"
            ]
            
            found_protections = 0
            for pattern in protected_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found_protections += 1
            
            if found_protections >= 2:
                logger.info("✅ Protected user logic appears to be properly implemented")
                return True
            else:
                logger.warning("⚠️  Protected user logic may be incomplete")
                return False
                
        except Exception as e:
            logger.error(f"Error checking protected user logic: {e}")
            return False

    def deploy_to_azure(self) -> bool:
        """Deploy to Azure and set up environment variables"""
        logger.info("🚀 Starting Azure deployment...")
        
        # Push to Azure remote
        success, output = self.run_command("git push azure master")
        if not success:
            logger.error(f"Failed to push to Azure: {output}")
            return False
            
        logger.info("✅ Successfully pushed to Azure")
        
        # Note: Environment variables should be set through Azure Portal
        logger.info("📋 Environment variables setup:")
        logger.info("    Please ensure the following environment variables are set in Azure:")
        
        required_env_vars = [
            "FLASK_SECRET_KEY",
            "ADMIN_PASSWORD", 
            "DEMO_USERNAME",
            "DEMO_PASSWORD",
            "SESSION_TIMEOUT",
            "PASSWORD_MIN_LENGTH"
        ]
        
        for var in required_env_vars:
            logger.info(f"    - {var}")
            
        return True

    def run_deployment(self, auto_commit: bool = False, commit_message: str = None) -> bool:
        """Run the complete deployment process"""
        logger.info("🎯 Starting AI Learning Tracker deployment process...")
        logger.info(f"📁 Working directory: {self.repo_path}")
        
        try:
            # Step 1: Check git status
            git_status = self.check_git_status()
            
            if git_status["has_changes"]:
                if auto_commit:
                    if not commit_message:
                        commit_message = f"Auto-commit: Security fixes and deployment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    if not self.commit_changes(commit_message):
                        logger.error("❌ Failed to commit changes. Aborting deployment.")
                        return False
                else:
                    logger.error("❌ Uncommitted changes detected. Please commit or stash them first.")
                    logger.info("💡 Use --auto-commit flag to automatically commit changes")
                    return False
            
            # Step 2: Security scan
            security_issues = self.scan_hardcoded_password_resets()
            if security_issues:
                high_severity = [issue for issue in security_issues if issue["severity"] == "HIGH"]
                if high_severity:
                    logger.error("❌ High severity security issues found. Please fix them before deployment.")
                    return False
                else:
                    logger.warning("⚠️  Medium severity issues found but continuing deployment...")
            
            # Step 3: Check protected user logic
            if not self.check_protected_user_logic():
                logger.warning("⚠️  Protected user logic verification failed, but continuing...")
            
            # Step 4: Deploy to Azure
            if not self.deploy_to_azure():
                logger.error("❌ Azure deployment failed")
                return False
            
            logger.info("🎉 Deployment completed successfully!")
            logger.info(f"🌐 Application URL: https://{self.azure_app_name}.azurewebsites.net")
            logger.info(f"📊 Admin Panel: https://{self.azure_app_name}.azurewebsites.net/admin")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment failed with error: {e}")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Learning Tracker Deployment Script")
    parser.add_argument("--auto-commit", action="store_true", 
                       help="Automatically commit uncommitted changes")
    parser.add_argument("--commit-message", type=str,
                       help="Custom commit message for auto-commit")
    parser.add_argument("--security-only", action="store_true",
                       help="Only run security scan without deployment")
    
    args = parser.parse_args()
    
    deployment_manager = DeploymentManager()
    
    if args.security_only:
        logger.info("🔒 Running security scan only...")
        issues = deployment_manager.scan_hardcoded_password_resets()
        protected_ok = deployment_manager.check_protected_user_logic()
        
        if not issues and protected_ok:
            logger.info("✅ Security scan completed - no issues found")
            return 0
        else:
            logger.warning("⚠️  Security scan completed - issues found")
            return 1
    else:
        success = deployment_manager.run_deployment(
            auto_commit=args.auto_commit,
            commit_message=args.commit_message
        )
        return 0 if success else 1

if __name__ == "__main__":
    exit(main())
