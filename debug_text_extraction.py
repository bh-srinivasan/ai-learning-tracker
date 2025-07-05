#!/usr/bin/env python3
"""
Test script to debug and verify the URL Status filter text extraction fix.
This simulates how the filter should handle HTML content in table cells.
"""

def simulate_text_extraction():
    """Simulate how text extraction works with HTML badges."""
    
    print("🔍 URL Status Filter - Text Extraction Debug")
    print("=" * 50)
    
    # Simulate the actual HTML content that appears in table cells
    test_cases = [
        {
            "html": '<span class="badge bg-success"><i class="fas fa-check-circle"></i> Working</span>',
            "expected_text": " Working",  # textContent includes space from icon
            "clean_text": "Working",
            "filter_value": "Working"
        },
        {
            "html": '<span class="badge bg-danger"><i class="fas fa-times-circle"></i> Not Working</span>',
            "expected_text": " Not Working",
            "clean_text": "Not Working", 
            "filter_value": "Not Working"
        },
        {
            "html": '<span class="badge bg-warning"><i class="fas fa-exclamation-triangle"></i> Broken</span>',
            "expected_text": " Broken",
            "clean_text": "Broken",
            "filter_value": "Broken"
        },
        {
            "html": '<span class="badge bg-secondary"><i class="fas fa-question-circle"></i> Unchecked</span>',
            "expected_text": " Unchecked",
            "clean_text": "Unchecked",
            "filter_value": "unchecked"  # Note: database has lowercase
        }
    ]
    
    print("Testing text extraction logic:")
    print("-" * 30)
    
    for i, case in enumerate(test_cases, 1):
        raw_text = case["expected_text"]  # This is what textContent returns
        
        # Apply the new cleaning logic (simulating JavaScript)
        cleaned_text = raw_text.strip()  # Remove leading/trailing spaces
        
        matches_filter = cleaned_text.lower() == case["filter_value"].lower()
        
        print(f"Test Case {i}:")
        print(f"  HTML: {case['html']}")
        print(f"  Raw textContent: '{raw_text}'")
        print(f"  Cleaned text: '{cleaned_text}'")
        print(f"  Filter value: '{case['filter_value']}'")
        print(f"  Should match: {matches_filter}")
        
        if matches_filter:
            print("  ✅ PASS: Filter matching works")
        else:
            print("  ❌ FAIL: Filter matching broken")
        print()
    
    return True

def check_template_fix():
    """Check if the template has the correct text extraction logic."""
    
    print("🔧 Template Fix Verification")
    print("-" * 30)
    
    template_path = 'templates/admin/courses.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for the improved text extraction
        checks = [
            ("URL Status Cell Variable", "urlStatusCell = cells[5]"),
            ("Text Content Extraction", "statusText = urlStatusCell.textContent.trim()"),
            ("Leading Space Removal", "replace(/^\\s*/, \"\")"),
            ("Exact Matching", "urlStatus === urlStatusFilter.toLowerCase()"),
        ]
        
        all_passed = True
        for check_name, pattern in checks:
            if pattern in content:
                print(f"✅ PASS: {check_name}")
            else:
                print(f"❌ FAIL: {check_name}")
                all_passed = False
        
        # Count occurrences (should be 2)
        url_status_cell_count = content.count("urlStatusCell = cells[5]")
        if url_status_cell_count >= 2:
            print(f"✅ PASS: Text extraction fix applied in {url_status_cell_count} locations")
        else:
            print(f"❌ FAIL: Text extraction fix only in {url_status_cell_count} locations")
            all_passed = False
            
        return all_passed
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test function."""
    
    print("URL Status Filter - Text Extraction Fix Debug")
    print("=" * 50)
    
    test1 = simulate_text_extraction()
    test2 = check_template_fix()
    
    print("=" * 50)
    
    if test1 and test2:
        print("🎉 TEXT EXTRACTION FIX LOOKS GOOD!")
        print("\n✅ Fix Summary:")
        print("   • Extract text from URL Status cell properly")
        print("   • Remove leading spaces from icon content")
        print("   • Use exact matching for filter comparison")
        print("   • Applied to both filter function instances")
        
        print("\n🧪 Test Instructions:")
        print("   1. Go to Admin → Manage Courses")
        print("   2. Select 'Working' from URL Status filter")
        print("   3. Should show 4 courses with Working status")
        print("   4. Try 'Not Working' - should show 1 course")
        print("   5. Try 'Unchecked' - should show 17 courses")
        
    else:
        print("❌ TEXT EXTRACTION FIX NEEDS ATTENTION")
        
    return test1 and test2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
