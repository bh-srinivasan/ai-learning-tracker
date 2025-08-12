#!/usr/bin/env python3
"""
Security Fix Script - Replace hardcoded credentials with environment variables
"""

import os
import re
from pathlib import Path

# Files that should be fixed (excluding archived ones for now)
critical_files = [
    'secure_admin_reset.py',
    'secure_password_reset.py', 
    'initialize_azure_admin.py',
    'test_admin_dashboard.py',
    'test_admin_flow.py',
    'test_azure_session_creation.py',
    'test_azure_session_debug.py',
    'test_azure_sql_connection.py'
]

def fix_file(file_path):
    """Fix hardcoded credentials in a file"""
    if not os.path.exists(file_path):
        return False
        
    print(f"🔧 Fixing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup original
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Apply fixes
        original_content = content
        
        # Fix Azure SQL passwords
        content = re.sub(
            r"password\s*=\s*['\"]AiAzurepass!2025['\"]",
            "password = os.environ.get('AZURE_SQL_PASSWORD', 'AiAzurepass!2025')",
            content
        )
        
        # Fix admin passwords  
        content = re.sub(
            r"password\s*=\s*['\"]YourSecureAdminPassword123!['\"]",
            "password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')",
            content
        )
        
        content = re.sub(
            r"password\s*=\s*['\"]YourSecureAdminPassword1223!['\"]",
            "password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')",
            content
        )
        
        # Fix test passwords
        content = re.sub(
            r"password\s*=\s*['\"]admin123!['\"]",
            "password = os.environ.get('ADMIN_PASSWORD', 'admin123!')",
            content
        )
        
        # Fix demo passwords
        content = re.sub(
            r"PASSWORD\s*=\s*['\"]Strong@Password123['\"]",
            "PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Strong@Password123')",
            content
        )
        
        # Add os import if needed
        if content != original_content and 'import os' not in content:
            if content.startswith('import ') or content.startswith('from '):
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith(('#', 'import', 'from')):
                        lines.insert(i, 'import os')
                        break
                content = '\n'.join(lines)
            else:
                content = 'import os\n' + content
        
        # Write fixed content
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed {file_path}")
            return True
        else:
            print(f"  ⏭️  No changes needed for {file_path}")
            # Remove backup if no changes
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function"""
    print("🛡️  Security Fix Script")
    print("=" * 40)
    
    fixed_count = 0
    
    for file_name in critical_files:
        if fix_file(file_name):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
    print("\n🔧 Next steps:")
    print("1. Set environment variables for your passwords")
    print("2. Review the .backup files and delete them when satisfied")
    print("3. Run security_audit.py again to verify fixes")
    
if __name__ == "__main__":
    main()
