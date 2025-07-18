#!/usr/bin/env python3
"""
Find duplicate Flask routes in app.py
"""

import re

def find_duplicate_routes():
    """Find duplicate route definitions in app.py"""
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Try with different encoding
        with open('app.py', 'r', encoding='latin-1') as f:
            lines = f.readlines()
    
    routes = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for route decorators
        if line.startswith('@app.route('):
            route_match = re.search(r"@app\.route\('([^']+)'", line)
            if route_match:
                route_path = route_match.group(1)
                
                if route_path in routes:
                    print(f"DUPLICATE ROUTE FOUND: {route_path}")
                    print(f"  First occurrence: Line {routes[route_path] + 1}")
                    print(f"  Duplicate: Line {i + 1}")
                    print(f"  Line content: {line}")
                    print()
                else:
                    routes[route_path] = i
    
    print(f"Total unique routes found: {len(routes)}")
    
    # Look for duplicate function names
    print("\nChecking for duplicate function names:")
    functions = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith('def ') and not line.startswith('def __'):
            func_match = re.search(r'def (\w+)\(', line)
            if func_match:
                func_name = func_match.group(1)
                
                if func_name in functions:
                    print(f"DUPLICATE FUNCTION: {func_name}")
                    print(f"  First: Line {functions[func_name] + 1}")
                    print(f"  Duplicate: Line {i + 1}")
                    print()
                else:
                    functions[func_name] = i

if __name__ == "__main__":
    find_duplicate_routes()
