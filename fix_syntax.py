#!/usr/bin/env python3
"""
Fix the syntax error in app.py line 952
"""

import re

def fix_syntax_error():
    """Fix the unterminated string literal in app.py"""
    
    # Read the file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic line
    # Look for the pattern with missing quote
    pattern = r"@app\.route\('/extend-session', methods=\['POST\]\)"
    replacement = r"@app.route('/extend-session', methods=['POST'])"
    
    # Try multiple patterns to catch the error
    patterns_to_fix = [
        (r"@app\.route\('/extend-session', methods=\['POST\]\)", r"@app.route('/extend-session', methods=['POST'])"),
        (r"methods=\['POST\]", r"methods=['POST']"),
        (r"'POST\]", r"'POST']"),
    ]
    
    original_content = content
    
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content)
        if content != original_content:
            print(f"Applied fix: {pattern} -> {replacement}")
            break
    
    # Write the file back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Syntax error fix applied successfully!")

if __name__ == "__main__":
    fix_syntax_error()
