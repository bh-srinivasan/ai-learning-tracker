#!/usr/bin/env python3
"""
Azure Deployment Security Audit
Comprehensive audit of all user-related operations for safe Azure deployment
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple

class AzureDeploymentSecurityAudit:
    """Audit all user management operations for Azure deployment safety"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.security_issues = []
        self.safe_operations = []
        self.recommendations = []
        
    def audit_user_management_operations(self) -> Dict[str, List[str]]:
        """Audit all user management operations in the codebase"""
        
        print("🔍 Auditing User Management Operations for Azure Deployment")
        print("=" * 65)
        
        # Files to audit
        python_files = list(self.workspace_path.glob("**/*.py"))
        
        # Dangerous operations to look for
        dangerous_patterns = [
            r"DELETE\s+FROM\s+users",
            r"DROP\s+TABLE\s+users",
            r"UPDATE\s+users\s+SET\s+password_hash",
            r"conn\.execute.*DELETE.*users",
            r"cursor\.execute.*DELETE.*users",
            r"conn\.execute.*UPDATE.*password",
            r"cursor\.execute.*UPDATE.*password",
            r"reset_user_password\(",
            r"delete_user\(",
            r"remove_user\(",
            r"bulk_password_reset",
            r"cleanup_database",
        ]
        
        # Safe operation patterns
        safe_patterns = [
            r"@password_reset_guard",
            r"@security_guard",
            r"SecurityGuard\.validate_operation",
            r"explicit_user_request=True",
            r"ui_triggered=True",
            r"require_admin",
            r"log_security_event",
        ]
        
        audit_results = {
            'dangerous_operations': [],
            'safe_operations': [],
            'unprotected_operations': [],
            'files_audited': []
        }
        
        for file_path in python_files:
            if file_path.name.startswith('test_') or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                audit_results['files_audited'].append(str(file_path.relative_to(self.workspace_path)))
                
                # Check for dangerous operations
                for pattern in dangerous_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        audit_results['dangerous_operations'].append({
                            'file': str(file_path.relative_to(self.workspace_path)),
                            'line': line_num,
                            'pattern': pattern,
                            'match': match.group().strip(),
                            'context': self._get_context(content, match.start(), match.end())
                        })
                
                # Check for safe operations
                for pattern in safe_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        audit_results['safe_operations'].append({
                            'file': str(file_path.relative_to(self.workspace_path)),
                            'pattern': pattern,
                        })
                        
            except Exception as e:
                print(f"⚠️  Warning: Could not audit {file_path}: {e}")
        
        return audit_results
    
    def _get_context(self, content: str, start: int, end: int, context_lines: int = 3) -> str:
        """Get context lines around a match"""
        lines = content.split('\n')
        match_line = content[:start].count('\n')
        
        start_line = max(0, match_line - context_lines)
        end_line = min(len(lines), match_line + context_lines + 1)
        
        context_lines_list = []
        for i in range(start_line, end_line):
            prefix = ">>> " if i == match_line else "    "
            context_lines_list.append(f"{prefix}{i+1:4d}: {lines[i]}")
        
        return '\n'.join(context_lines_list)
    
    def check_environment_safeguards(self) -> List[Dict[str, str]]:
        """Check for proper environment-based safeguards"""
        
        print("\n🛡️  Checking Environment-Based Safeguards")
        print("-" * 45)
        
        safeguard_checks = []
        
        # Check app.py for environment guards
        app_py = self.workspace_path / "app.py"
        if app_py.exists():
            with open(app_py, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for production environment checks
            if "FLASK_ENV" in content or "NODE_ENV" in content:
                safeguard_checks.append({
                    'check': 'Environment Variable Detection',
                    'status': '✅ PASS',
                    'details': 'Environment variables are used for configuration'
                })
            else:
                safeguard_checks.append({
                    'check': 'Environment Variable Detection',
                    'status': '❌ FAIL',
                    'details': 'No environment variable checks found'
                })
            
            # Check for security guard imports
            if "from security_guard import" in content:
                safeguard_checks.append({
                    'check': 'Security Guard Integration',
                    'status': '✅ PASS',
                    'details': 'Security guard system is imported and used'
                })
            else:
                safeguard_checks.append({
                    'check': 'Security Guard Integration',
                    'status': '❌ FAIL',
                    'details': 'Security guard system not properly integrated'
                })
        
        # Check security_guard.py for production safeguards
        security_guard_py = self.workspace_path / "security_guard.py"
        if security_guard_py.exists():
            with open(security_guard_py, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "is_development" in content and "production" in content.lower():
                safeguard_checks.append({
                    'check': 'Production Environment Protection',
                    'status': '✅ PASS',
                    'details': 'Production environment protection implemented'
                })
            else:
                safeguard_checks.append({
                    'check': 'Production Environment Protection',
                    'status': '❌ FAIL',
                    'details': 'No production environment protection found'
                })
        
        return safeguard_checks
    
    def check_hardcoded_credentials(self) -> List[Dict[str, str]]:
        """Check for hardcoded credentials or user references"""
        
        print("\n🔐 Checking for Hardcoded Credentials")
        print("-" * 40)
        
        credential_issues = []
        
        # Patterns that indicate hardcoded credentials
        hardcoded_patterns = [
            r"password\s*=\s*['\"][^'\"]*['\"]",
            r"Password123",
            r"admin.*password.*=",
            r"demo.*password.*=",
            r"bharath",  # Specific user references
            r"hardcoded",
        ]
        
        python_files = list(self.workspace_path.glob("**/*.py"))
        
        for file_path in python_files:
            if file_path.name.startswith('test_') or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in hardcoded_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        credential_issues.append({
                            'file': str(file_path.relative_to(self.workspace_path)),
                            'line': line_num,
                            'issue': match.group().strip(),
                            'severity': 'HIGH' if 'password' in match.group().lower() else 'MEDIUM'
                        })
                        
            except Exception as e:
                print(f"⚠️  Warning: Could not check {file_path}: {e}")
        
        return credential_issues
    
    def generate_deployment_report(self) -> str:
        """Generate comprehensive deployment readiness report"""
        
        print("\n📋 Generating Azure Deployment Readiness Report")
        print("=" * 50)
        
        # Run all audits
        user_ops_audit = self.audit_user_management_operations()
        env_safeguards = self.check_environment_safeguards()
        credential_issues = self.check_hardcoded_credentials()
        
        # Generate report
        report = []
        report.append("# Azure Deployment Security Audit Report")
        report.append(f"Generated: {os.environ.get('DATE', 'Unknown')}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        
        dangerous_count = len(user_ops_audit['dangerous_operations'])
        safe_count = len(user_ops_audit['safe_operations'])
        credential_count = len(credential_issues)
        
        if dangerous_count == 0 and credential_count == 0:
            report.append("✅ **DEPLOYMENT APPROVED**: No critical security issues found")
        elif dangerous_count > 0:
            report.append("❌ **DEPLOYMENT BLOCKED**: Critical user management issues found")
        else:
            report.append("⚠️  **DEPLOYMENT CAUTION**: Minor issues require attention")
        
        report.append("")
        
        # User Operations Audit
        report.append("## User Management Operations Audit")
        report.append("")
        report.append(f"- **Files Audited**: {len(user_ops_audit['files_audited'])}")
        report.append(f"- **Dangerous Operations**: {dangerous_count}")
        report.append(f"- **Safe Operations**: {safe_count}")
        report.append("")
        
        if user_ops_audit['dangerous_operations']:
            report.append("### ⚠️  Dangerous Operations Found")
            report.append("")
            for op in user_ops_audit['dangerous_operations']:
                report.append(f"**File**: `{op['file']}` (Line {op['line']})")
                report.append(f"**Pattern**: `{op['pattern']}`")
                report.append(f"**Match**: `{op['match']}`")
                report.append("```")
                report.append(op['context'])
                report.append("```")
                report.append("")
        
        # Environment Safeguards
        report.append("## Environment Safeguards")
        report.append("")
        for check in env_safeguards:
            report.append(f"- **{check['check']}**: {check['status']}")
            report.append(f"  {check['details']}")
        report.append("")
        
        # Credential Issues
        if credential_issues:
            report.append("## Hardcoded Credential Issues")
            report.append("")
            for issue in credential_issues:
                severity_icon = "🔴" if issue['severity'] == 'HIGH' else "🟡"
                report.append(f"{severity_icon} **{issue['file']}** (Line {issue['line']}): `{issue['issue']}`")
            report.append("")
        
        # Recommendations
        report.append("## Deployment Recommendations")
        report.append("")
        if dangerous_count > 0:
            report.append("1. **❌ BLOCK DEPLOYMENT**: Review and secure dangerous operations")
        if credential_count > 0:
            report.append("2. **🔐 Fix Credentials**: Replace hardcoded credentials with environment variables")
        
        report.append("3. **✅ Verify Security Guards**: Ensure all user operations are protected")
        report.append("4. **🧪 Run Tests**: Execute all security tests before deployment")
        report.append("5. **📝 Document Changes**: Update deployment documentation")
        
        return '\n'.join(report)

def run_azure_deployment_audit():
    """Run comprehensive Azure deployment security audit"""
    
    workspace_path = os.getcwd()
    auditor = AzureDeploymentSecurityAudit(workspace_path)
    
    print("🚀 Azure Deployment Security Audit")
    print("=" * 40)
    print(f"Workspace: {workspace_path}")
    print("")
    
    # Generate and display report
    report = auditor.generate_deployment_report()
    
    # Save report to file
    report_file = Path(workspace_path) / "AZURE_DEPLOYMENT_AUDIT_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Full report saved to: {report_file}")
    
    # Display key findings
    print("\n" + "=" * 50)
    print("KEY FINDINGS SUMMARY")
    print("=" * 50)
    
    # Quick audit for immediate feedback
    user_ops = auditor.audit_user_management_operations()
    credentials = auditor.check_hardcoded_credentials()
    
    dangerous_ops = len(user_ops['dangerous_operations'])
    credential_issues = len(credentials)
    
    if dangerous_ops == 0 and credential_issues == 0:
        print("✅ DEPLOYMENT READY: No critical issues found")
        return True
    else:
        print(f"⚠️  DEPLOYMENT ISSUES: {dangerous_ops} dangerous operations, {credential_issues} credential issues")
        return False

if __name__ == "__main__":
    success = run_azure_deployment_audit()
    if not success:
        exit(1)
