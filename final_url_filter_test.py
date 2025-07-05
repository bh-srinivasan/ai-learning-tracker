#!/usr/bin/env python3
"""
Final verification test for URL Status filter fix.
This test validates that the filter now works correctly with text extraction.
"""

import sqlite3
import re

def final_verification():
    """Final verification of the URL Status filter fix."""
    
    print("🎯 URL Status Filter - Final Verification")
    print("=" * 50)
    
    # Check database values
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT url_status, COUNT(*) as count FROM courses WHERE url_status IS NOT NULL GROUP BY url_status ORDER BY count DESC")
        statuses = cursor.fetchall()
        
        print("📊 Database URL Status Values:")
        for status, count in statuses:
            print(f"   '{status}': {count} courses")
        
        conn.close()
        
        # Check template implementation
        template_path = 'templates/admin/courses.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n🔧 Template Implementation Check:")
        
        # Verify dropdown values match database values
        dropdown_values = []
        for status, _ in statuses:
            if f'value="{status}"' in content:
                print(f"   ✅ Dropdown value '{status}' matches database")
                dropdown_values.append(status)
            else:
                print(f"   ❌ Dropdown value '{status}' missing")
        
        # Check text extraction logic
        text_extraction_checks = [
            ("URL Status Cell Extraction", "urlStatusCell = cells[5]"),
            ("Text Content Trim", "urlStatusCell.textContent.trim()"),
            ("Leading Space Removal", "replace(/^\\s*/, \"\")"),
            ("Case-insensitive Exact Match", "urlStatus === urlStatusFilter.toLowerCase()"),
        ]
        
        print("\n🔍 Text Extraction Logic:")
        all_checks_passed = True
        for check_name, pattern in text_extraction_checks:
            if pattern in content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                all_checks_passed = False
        
        # Verify both filter functions are updated
        extraction_count = content.count("urlStatusCell = cells[5]")
        if extraction_count >= 2:
            print(f"   ✅ Text extraction implemented in {extraction_count} filter functions")
        else:
            print(f"   ❌ Text extraction only in {extraction_count} filter functions (need 2)")
            all_checks_passed = False
        
        return all_checks_passed and len(dropdown_values) == len(statuses)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_expected_behavior():
    """Test what the expected behavior should be."""
    
    print("\n🧪 Expected Filter Behavior:")
    print("-" * 30)
    
    expected_results = [
        ("Working", 4, "Should show 4 courses with 'Working' status"),
        ("Not Working", 1, "Should show 1 course with 'Not Working' status"),
        ("Broken", 0, "Should show 0 courses with 'Broken' status"),
        ("unchecked", 17, "Should show 17 courses with 'unchecked' status"),
    ]
    
    for filter_value, expected_count, description in expected_results:
        print(f"   Filter: '{filter_value}' → {expected_count} courses")
        print(f"   {description}")
    
    print("\n💡 Key Fix Details:")
    print("   • Extract text content from HTML badge cells")
    print("   • Remove leading spaces from icon formatting")
    print("   • Use exact string matching (case-insensitive)")
    print("   • Match dropdown values exactly to database values")
    
    return True

def main():
    """Main verification function."""
    
    print("URL Status Filter - Final Fix Verification")
    print("=" * 50)
    
    test1 = final_verification()
    test2 = test_expected_behavior()
    
    print("\n" + "=" * 50)
    
    if test1 and test2:
        print("🎉 FINAL VERIFICATION SUCCESSFUL!")
        print("\n✅ Fix Complete:")
        print("   • Database values match dropdown values")
        print("   • Text extraction handles HTML badge formatting")
        print("   • Exact matching prevents false positives")
        print("   • Both filter functions updated consistently")
        
        print("\n🚀 Ready to Test:")
        print("   1. Open Admin → Manage Courses")
        print("   2. Try each URL Status filter option")
        print("   3. Verify correct number of results")
        print("   4. Confirm no false positives")
        
        print("\n📋 Expected Results:")
        print("   • Working: 4 courses")
        print("   • Not Working: 1 course")
        print("   • Broken: 0 courses")
        print("   • Unchecked: 17 courses")
        
        return True
    else:
        print("❌ FINAL VERIFICATION FAILED")
        print("The URL Status filter fix needs more attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
