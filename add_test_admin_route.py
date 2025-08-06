#!/usr/bin/env python3
"""Add a test admin route to isolate template rendering issues"""

# This script will temporarily add a test route to app.py to debug template rendering

import re

# Read the current app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a simple test admin route before the existing admin route
test_route = '''
@app.route('/admin-template-test')
def admin_template_test():
    """Simple admin template test route to debug template rendering"""
    try:
        # Static test data
        return render_template('admin/index.html',
                             total_users=99,
                             total_courses=88,
                             total_learnings=77,
                             recent_users=[])
    except Exception as e:
        return f"<h1>Template Error</h1><p>Error: {str(e)}</p><pre>{repr(e)}</pre>"

'''

# Find the existing admin route and insert the test route before it
admin_route_pattern = r'(@app\.route\(\'/admin\'\)\ndef admin_dashboard\(\):)'
if re.search(admin_route_pattern, content):
    new_content = re.sub(admin_route_pattern, test_route + r'\1', content)
    
    # Write back to app.py
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Test admin route added to app.py")
    print("🔄 Restart Flask app to activate test route")
    print("🌐 Visit http://localhost:5000/admin-test to test template rendering")
else:
    print("❌ Could not find admin route pattern in app.py")
