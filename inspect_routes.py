#!/usr/bin/env python3
"""
Check all registered routes in the Flask app
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def list_routes():
    """List all registered routes in the Flask app"""
    print("🔍 Registered Routes in Flask App:")
    print("=" * 50)
    
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"  {rule.endpoint:<30} {methods:<15} {rule.rule}")
    
    print("\n🎯 Specifically looking for missing routes:")
    expected_routes = [
        'export_courses',
        'update_completion_date', 
        'complete_course',
        'mark_complete',
        'my_courses',
        'admin_dashboard'  # our new route
    ]
    
    actual_endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]
    
    for route in expected_routes:
        if route in actual_endpoints:
            print(f"  ✅ {route}")
        else:
            print(f"  ❌ {route} - MISSING")

if __name__ == "__main__":
    list_routes()
