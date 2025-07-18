#!/usr/bin/env python3
"""
Remove duplicate admin route from app.py
"""

def remove_duplicate_admin_route():
    """Remove the duplicate admin route definition"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line numbers of both admin route definitions
    first_admin_line = None
    second_admin_line = None
    
    for i, line in enumerate(lines):
        if line.strip() == "@app.route('/admin')" and 'admin_dashboard' in lines[i+1]:
            if first_admin_line is None:
                first_admin_line = i
                print(f"First admin route found at line {i+1}")
            else:
                second_admin_line = i
                print(f"Second admin route found at line {i+1}")
                break
    
    if first_admin_line is not None and second_admin_line is not None:
        # Remove the second admin route definition
        # Find where it ends by looking for the next route or function
        end_line = second_admin_line + 1
        
        # Look for the end of the admin_dashboard function
        brace_count = 0
        in_function = False
        
        for i in range(second_admin_line + 2, len(lines)):  # Start after function definition
            line = lines[i].strip()
            
            # If we hit another @app.route or def at the root level, we're done
            if (line.startswith('@app.route') or 
                (line.startswith('def ') and not line.startswith('    '))):
                end_line = i
                break
            
            # Check for end of file
            if i == len(lines) - 1:
                end_line = i + 1
                break
        
        print(f"Removing lines {second_admin_line + 1} to {end_line}")
        
        # Remove the duplicate section
        new_lines = lines[:second_admin_line] + lines[end_line:]
        
        # Write back to file
        with open('app.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"Successfully removed duplicate admin route!")
        print(f"Removed {end_line - second_admin_line} lines")
        
    else:
        print("Could not find duplicate admin routes")

if __name__ == "__main__":
    remove_duplicate_admin_route()
