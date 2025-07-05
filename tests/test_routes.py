#!/usr/bin/env python3
"""
Test script to verify Flask routes are properly registered
"""
import sys
sys.path.append('.')

from app import app

def test_routes():
    """Test if all admin routes are properly registered"""
    print("Testing Flask route registration...")
    print("=" * 50)
    
    # Get all registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': rule.rule
        })
    
    # Filter admin routes
    admin_routes = [r for r in routes if r['endpoint'].startswith('admin.')]
    
    print(f"Found {len(admin_routes)} admin routes:")
    print("-" * 30)
    
    for route in sorted(admin_routes, key=lambda x: x['endpoint']):
        print(f"Endpoint: {route['endpoint']}")
        print(f"  Rule: {route['rule']}")
        print(f"  Methods: {route['methods']}")
        print()
    
    # Check specifically for url_validation
    url_validation_routes = [r for r in admin_routes if 'url_validation' in r['endpoint']]
    
    if url_validation_routes:
        print("✅ URL validation routes found:")
        for route in url_validation_routes:
            print(f"  - {route['endpoint']}: {route['rule']}")
    else:
        print("❌ No URL validation routes found!")
    
    print("\n" + "=" * 50)
    
    # Test URL building with app context
    print("Testing URL building...")
    
    with app.app_context():
        with app.test_request_context():
            try:
                from flask import url_for
                url = url_for('admin.url_validation')
                print(f"✅ SUCCESS: admin.url_validation -> {url}")
            except Exception as e:
                print(f"❌ ERROR building admin.url_validation: {e}")
                
            # Test other admin routes
            test_endpoints = [
                'admin.index',
                'admin.courses', 
                'admin.users'
            ]
            
            for endpoint in test_endpoints:
                try:
                    url = url_for(endpoint)
                    print(f"✅ SUCCESS: {endpoint} -> {url}")
                except Exception as e:
                    print(f"❌ ERROR building {endpoint}: {e}")

def test_admin_blueprint():
    """Test if admin blueprint is properly registered"""
    print("\nTesting Blueprint Registration...")
    print("=" * 50)
    
    # Check if admin blueprint is registered
    blueprints = app.blueprints
    
    if 'admin' in blueprints:
        print("✅ Admin blueprint is registered")
        admin_bp = blueprints['admin']
        print(f"  Name: {admin_bp.name}")
        print(f"  URL prefix: {admin_bp.url_prefix}")
        
        # Check blueprint's registered routes
        blueprint_routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('admin.'):
                blueprint_routes.append(rule)
        
        print(f"  Routes registered: {len(blueprint_routes)}")
        
    else:
        print("❌ Admin blueprint is NOT registered!")
        print("Available blueprints:")
        for bp_name in blueprints:
            print(f"  - {bp_name}")

if __name__ == "__main__":
    test_admin_blueprint()
    test_routes()
