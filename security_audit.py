#!/usr/bin/env python3
"""
Security Audit Script for AI Learning Tracker
Scans all files for potential security issues including hardcoded credentials
"""

import os
import re
import sys
from pathlib import Path

class SecurityAuditor:
    def __init__(self, root_path="."):
        self.root_path = Path(root_path)
        self.issues = []
        
        # Patterns to look for
        self.password_patterns = [
            r'password\s*=\s*[\'"][^\'"]+[\'"]',
            r'Password\s*=\s*[\'"][^\'"]+[\'"]',
            r'PASSWORD\s*=\s*[\'"][^\'"]+[\'"]',
            r'pwd\s*=\s*[\'"][^\'"]+[\'"]',
            r'secret\s*=\s*[\'"][^\'"]+[\'"]',
            r'key\s*=\s*[\'"][^\'"]+[\'"]',
            r'token\s*=\s*[\'"][^\'"]+[\'"]',
        ]
        
        # File extensions to check
        self.extensions = {'.py', '.ps1', '.sh', '.sql', '.js', '.ts', '.json', '.yaml', '.yml', '.env'}
        
        # Exclude patterns
        self.exclude_dirs = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv', 'venv64',
            'temp-package', 'Coding', '.pytest_cache'
        }
        
        self.exclude_files = {
            'security_audit.py', 'package-lock.json', 'requirements.txt'
        }

    def is_excluded(self, path):
        """Check if path should be excluded from scanning"""
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in path.parts:
                return True
        return path.name in self.exclude_files

    def scan_file(self, file_path):
        """Scan a single file for security issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            for line_num, line in enumerate(lines, 1):
                # Check for password patterns
                for pattern in self.password_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's a template or environment variable reference
                        if self.is_safe_pattern(match.group(0)):
                            continue
                            
                        self.issues.append({
                            'file': str(file_path),
                            'line': line_num,
                            'issue': 'Potential hardcoded credential',
                            'content': match.group(0),
                            'severity': 'HIGH'
                        })
                        
                # Check for other security patterns
                if 'SECRET_KEY' in line and '=' in line and not '$' in line and not 'os.environ' in line:
                    if not self.is_safe_pattern(line):
                        self.issues.append({
                            'file': str(file_path),
                            'line': line_num,
                            'issue': 'Hardcoded secret key',
                            'content': line.strip(),
                            'severity': 'HIGH'
                        })
                        
        except Exception as e:
            print(f"⚠️  Could not scan {file_path}: {e}")

    def is_safe_pattern(self, text):
        """Check if the pattern is safe (template, env var, etc.)"""
        safe_indicators = [
            'your-', 'your_', 'YOUR_',
            'template', 'example', 'sample',
            '$', '${', '%',
            'os.environ', 'getenv',
            '[SECURE_PASSWORD]', '[PASSWORD]',
            'environment', 'env'
        ]
        
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in safe_indicators)

    def scan_directory(self):
        """Scan all files in the directory"""
        print("🔍 Starting security audit...")
        print(f"📁 Scanning: {self.root_path.absolute()}")
        print()
        
        scanned_files = 0
        
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file() and not self.is_excluded(file_path):
                if file_path.suffix.lower() in self.extensions:
                    self.scan_file(file_path)
                    scanned_files += 1
                    
        print(f"📊 Scanned {scanned_files} files")
        return scanned_files

    def generate_report(self):
        """Generate security audit report"""
        print("\n" + "="*70)
        print("🛡️  SECURITY AUDIT REPORT")
        print("="*70)
        
        if not self.issues:
            print("✅ NO SECURITY ISSUES FOUND!")
            print("\n🎉 All files passed security audit.")
            return
            
        # Group issues by severity
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        
        print(f"\n🚨 FOUND {len(self.issues)} POTENTIAL SECURITY ISSUES")
        print(f"   - HIGH severity: {len(high_issues)}")
        
        print("\n" + "-"*70)
        print("DETAILED FINDINGS:")
        print("-"*70)
        
        for i, issue in enumerate(self.issues, 1):
            severity_icon = "🔴" if issue['severity'] == 'HIGH' else "🟡"
            print(f"\n{severity_icon} Issue #{i} - {issue['severity']} SEVERITY")
            print(f"   📁 File: {issue['file']}")
            print(f"   📍 Line: {issue['line']}")
            print(f"   ⚠️  Issue: {issue['issue']}")
            print(f"   💾 Content: {issue['content'][:100]}...")
            
        print("\n" + "="*70)
        print("🔧 RECOMMENDATIONS:")
        print("="*70)
        print("1. Replace hardcoded credentials with environment variables")
        print("2. Use os.environ.get() or similar secure methods")
        print("3. Add sensitive files to .gitignore")
        print("4. Use Azure Key Vault or similar services for production")
        print("5. Review and update all flagged files immediately")
        
        return len(self.issues)

def main():
    """Main function"""
    print("🛡️  AI Learning Tracker - Security Audit")
    print("="*50)
    
    auditor = SecurityAuditor()
    auditor.scan_directory()
    issue_count = auditor.generate_report()
    
    # Exit with appropriate code
    if issue_count > 0:
        print(f"\n❌ Security audit failed with {issue_count} issues")
        sys.exit(1)
    else:
        print("\n✅ Security audit passed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
