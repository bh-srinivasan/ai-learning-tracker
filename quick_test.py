#!/usr/bin/env python3
"""
Quick test to verify URL status filter logic
"""

def test_filter_logic():
    """Test the filter logic with sample data."""
    
    print("🧪 URL Status Filter Logic Test")
    print("=" * 40)
    
    # Simulate the actual text content from HTML badges
    test_cases = [
        (" Working", "working"),  # Icon space + text → cleaned
        (" Not Working", "not working"),  # Icon space + text → cleaned
        (" Unchecked", "unchecked"),  # Icon space + text → cleaned
        ("Working", "working"),  # No leading space
        ("Not Working", "not working"),  # No leading space
    ]
    
    print("Text Cleaning Test:")
    for raw_text, expected in test_cases:
        # Simulate JavaScript: statusText.replace(/^\s*/, "").toLowerCase()
        cleaned = raw_text.strip()  # Remove leading/trailing spaces
        # In JavaScript, /^\s*/ removes leading whitespace
        import re
        js_cleaned = re.sub(r'^\s*', '', raw_text).lower()
        
        print(f"  Raw: '{raw_text}' → Cleaned: '{js_cleaned}' (Expected: '{expected}')")
        print(f"    Match: {js_cleaned == expected}")
    
    print("\nFilter Matching Test:")
    filter_tests = [
        ("working", "working", True),
        ("working", "not working", False),
        ("not working", "working", False),
        ("not working", "not working", True),
        ("unchecked", "unchecked", True),
        ("broken", "broken", True),
    ]
    
    for filter_val, text_val, expected in filter_tests:
        result = text_val == filter_val
        status = "✅" if result == expected else "❌"
        print(f"  {status} Filter '{filter_val}' vs Text '{text_val}' → {result}")

if __name__ == "__main__":
    test_filter_logic()
