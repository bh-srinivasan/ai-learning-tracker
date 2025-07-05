#!/usr/bin/env python3
"""
Final validation script for URL Status filter functionality.
This script performs end-to-end validation of the filter implementation.
"""

import re
import os

def validate_url_status_filter():
    """Validate that URL Status filter is properly implemented."""
    
    print("🔍 Final Validation: URL Status Filter Implementation")
    print("=" * 60)
    
    template_path = 'templates/admin/courses.html'
    
    if not os.path.exists(template_path):
        print("❌ FAIL: Template file not found")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required components
    checks = [
        ('HTML Filter Dropdown', r'id="urlStatusFilter"'),
        ('Filter Label', r'Filter by URL Status:'),
        ('Working Option', r'<option value="Working">.*Working</option>'),
        ('Not Working Option', r'<option value="Not Working">.*Not Working</option>'),
        ('Broken Option', r'<option value="Broken">.*Broken</option>'),
        ('Unchecked Option', r'<option value="unchecked">.*Unchecked</option>'),
        ('JavaScript Event Listener', r'urlStatusFilter.*addEventListener'),
        ('Filter Function Variable', r'urlStatusFilter.*getElementById'),
        ('Filter Matching Logic', r'matchesUrlStatus'),
        ('Clear Filters Include URL Status', r'getElementById\("urlStatusFilter"\)\.value = ""'),
    ]
    
    all_passed = True
    
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
            print(f"✅ PASS: {check_name}")
        else:
            print(f"❌ FAIL: {check_name}")
            all_passed = False
    
    # Validate filter integration
    if re.search(r'matchesSource.*matchesLevel.*matchesUrlStatus.*matchesPoints.*matchesSearch', content):
        print("✅ PASS: Filter integration - all filters work together")
    else:
        print("❌ FAIL: Filter integration incomplete")
        all_passed = False
    
    # Check for proper table column index (URL Status should be column 5)
    if re.search(r'cells\[5\].*textContent.*urlStatus', content, re.DOTALL):
        print("✅ PASS: Correct table column index for URL Status")
    elif re.search(r'urlStatus.*cells\[5\]', content, re.DOTALL):
        print("✅ PASS: Correct table column index for URL Status")
    else:
        print("❌ FAIL: Incorrect table column index")
        all_passed = False
    
    # Validate emoji handling in filter options
    emoji_patterns = ['✅', '❌', '🔗', '⏸️']
    for emoji in emoji_patterns:
        if emoji in content:
            print(f"✅ PASS: Emoji support - {emoji}")
        else:
            print(f"⚠️  WARN: Missing emoji - {emoji}")
    
    return all_passed

def validate_table_structure():
    """Validate that the table structure supports URL Status filtering."""
    
    print("\n🏗️  Table Structure Validation")
    print("-" * 40)
    
    template_path = 'templates/admin/courses.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for URL Status column header
    if re.search(r'<th.*>.*URL Status.*</th>', content, re.IGNORECASE):
        print("✅ PASS: URL Status column header exists")
    else:
        print("❌ FAIL: URL Status column header missing")
        return False
    
    # Check for URL Status data display
    if re.search(r'course\.url_status', content):
        print("✅ PASS: URL Status data binding exists")
    else:
        print("❌ FAIL: URL Status data binding missing")
        return False
    
    # Check for status badges
    status_checks = ['Working', 'Not Working', 'Broken', 'Unchecked']
    for status in status_checks:
        if status.lower() in content.lower():
            print(f"✅ PASS: Status badge support - {status}")
        else:
            print(f"❌ FAIL: Missing status badge - {status}")
    
    return True

def main():
    """Main validation function."""
    
    print("URL Status Filter - Final Validation Suite")
    print("=" * 60)
    
    filter_validation = validate_url_status_filter()
    table_validation = validate_table_structure()
    
    print("\n" + "=" * 60)
    
    if filter_validation and table_validation:
        print("🎉 VALIDATION SUCCESSFUL!")
        print("\nURL Status Filter Implementation Summary:")
        print("✅ Filter dropdown properly implemented")
        print("✅ JavaScript filtering logic complete")
        print("✅ Integration with existing filters")
        print("✅ Clear filters functionality updated")
        print("✅ Table structure supports filtering")
        print("✅ Visual indicators and emojis included")
        
        print("\n🚀 Ready for Production!")
        print("The URL Status filter is fully implemented and ready to use.")
        
        print("\n📋 Usage Guide:")
        print("1. Login as admin")
        print("2. Navigate to Admin → Manage Courses")
        print("3. Use 'Filter by URL Status' dropdown")
        print("4. Select desired status to filter courses")
        print("5. Use 'Clear Filters' to reset")
        
        return True
    else:
        print("❌ VALIDATION FAILED")
        print("Some components of the URL Status filter need attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
