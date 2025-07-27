"""
Integration script to add upload reports blueprint to main app
Run this once to integrate the upload reports feature
"""

import re

def integrate_upload_reports():
    """Add the upload reports blueprint to app.py"""
    
    # Read the current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already integrated
    if 'admin_reports_routes' in content:
        print("✅ Upload reports already integrated!")
        return
    
    # Find the first blueprint import section
    import_pattern = r'(from admin\.routes import admin_bp\n)'
    if re.search(import_pattern, content):
        # Add the import
        content = re.sub(
            import_pattern,
            r'\1from admin_reports_routes import admin_reports_bp  # Upload reports admin interface\n',
            content,
            count=1
        )
        
        # Add the blueprint registration
        register_pattern = r'(app\.register_blueprint\(admin_bp\)\n)'
        content = re.sub(
            register_pattern,
            r'\1app.register_blueprint(admin_reports_bp)\n',
            content,
            count=1
        )
        
        # Write back
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Upload reports blueprint integrated successfully!")
        print("📋 The following has been added:")
        print("   - Import: from admin_reports_routes import admin_reports_bp")
        print("   - Registration: app.register_blueprint(admin_reports_bp)")
        print("🔗 Access upload reports at: /admin/reports/")
        
    else:
        print("❌ Could not find blueprint import section in app.py")
        print("💡 Please manually add the following lines:")
        print("   Import: from admin_reports_routes import admin_reports_bp")
        print("   Register: app.register_blueprint(admin_reports_bp)")

if __name__ == "__main__":
    integrate_upload_reports()
