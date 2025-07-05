#!/usr/bin/env python3
"""
Test the new simplified URL status extraction logic
"""

import re

def test_new_logic():
    """Test the new text extraction logic."""
    
    print("🧪 New URL Status Extraction Logic Test")
    print("=" * 45)
    
    # Test cases simulating actual HTML content
    test_cases = [
        (" Working", "working"),  # Icon + space + text
        (" Not Working", "not working"),  # Icon + space + text
        (" Broken", "broken"),  # Icon + space + text  
        (" Unchecked", "unchecked"),  # Icon + space + text
        ("✓ Working", "working"),  # Different icon
        ("✗ Not Working", "not working"),  # Different icon
        ("? Unchecked", "unchecked"),  # Different icon
    ]
    
    print("Text Extraction Test:")
    for raw_text, expected in test_cases:
        # Simulate new JavaScript logic
        # Remove all non-letter characters except spaces, then trim
        cleaned = re.sub(r'[^\w\s]', '', raw_text).strip().lower()
        
        # Handle specific cases
        if 'working' in cleaned and 'not' not in cleaned:
            result = 'working'
        elif 'not' in cleaned and 'working' in cleaned:
            result = 'not working'
        elif 'broken' in cleaned:
            result = 'broken'
        elif 'unchecked' in cleaned:
            result = 'unchecked'
        else:
            result = cleaned
            
        match = result == expected
        status = "✅" if match else "❌"
        
        print(f"  {status} '{raw_text}' → '{cleaned}' → '{result}' (expected: '{expected}')")
    
    print("\nFilter Matching Test:")
    filter_tests = [
        ("working", "working", True),
        ("working", "not working", False), 
        ("not working", "not working", True),
        ("not working", "working", False),
        ("broken", "broken", True),
        ("unchecked", "unchecked", True),
    ]
    
    for filter_val, extracted_val, expected in filter_tests:
        result = extracted_val == filter_val
        status = "✅" if result == expected else "❌"
        print(f"  {status} Filter '{filter_val}' vs Extracted '{extracted_val}' → {result}")

if __name__ == "__main__":
    test_new_logic()
