#!/usr/bin/env python3
"""
Test script to verify the URL Status filter exact matching fix.
This script validates that filtering by "Working" only shows "Working" courses,
not "Not Working" courses.
"""

import sqlite3
import sys
import re

def test_url_status_exact_matching():
    """Test that URL Status filter uses exact matching, not partial matching."""
    
    print("🔧 Testing URL Status Filter - Exact Matching Fix")
    print("=" * 55)
    
    # First, let's check the database to see what URL statuses we have
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all distinct URL statuses
        cursor.execute("SELECT DISTINCT url_status, COUNT(*) as count FROM courses WHERE url_status IS NOT NULL GROUP BY url_status")
        url_statuses = cursor.fetchall()
        
        print("📊 Current URL Status Distribution:")
        for status in url_statuses:
            print(f"   '{status['url_status']}': {status['count']} courses")
        
        # Test specific cases that were problematic
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE url_status = 'Working'")
        working_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE url_status = 'Not Working'")
        not_working_count = cursor.fetchone()['count']
        
        print(f"\n🔍 Specific Counts:")
        print(f"   Exactly 'Working': {working_count} courses")
        print(f"   Exactly 'Not Working': {not_working_count} courses")
        
        conn.close()
        
        # Now check the template file for correct filtering logic
        template_path = 'templates/admin/courses.html'
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that we're using exact matching (===) instead of includes()
        exact_match_patterns = [
            r'urlStatus\.trim\(\)\.toLowerCase\(\)\s*===\s*urlStatusFilter\.toLowerCase\(\)',
            r'matchesUrlStatus.*===.*urlStatusFilter'
        ]
        
        has_exact_matching = False
        for pattern in exact_match_patterns:
            if re.search(pattern, content):
                has_exact_matching = True
                print(f"✅ PASS: Found exact matching pattern")
                break
        
        if not has_exact_matching:
            print("❌ FAIL: Exact matching pattern not found")
            return False
        
        # Check that we removed the problematic includes() pattern
        problematic_patterns = [
            r'urlStatus\.includes\(urlStatusFilter',
            r'urlStatusFilter\.replace\(/\[✅❌🔗⏸️\]'
        ]
        
        has_problematic_code = False
        for pattern in problematic_patterns:
            if re.search(pattern, content):
                has_problematic_code = True
                print(f"❌ FAIL: Still contains problematic pattern: {pattern}")
        
        if not has_problematic_code:
            print("✅ PASS: Removed problematic includes() patterns")
        
        # Count how many times the fix is applied (should be 2 - one in each filter function)
        exact_match_count = len(re.findall(r'urlStatus\.trim\(\)\.toLowerCase\(\)\s*===\s*urlStatusFilter\.toLowerCase\(\)', content))
        
        if exact_match_count >= 2:
            print(f"✅ PASS: Exact matching applied in {exact_match_count} locations")
        else:
            print(f"❌ FAIL: Exact matching only found in {exact_match_count} locations (expected 2+)")
            return False
        
        return True and not has_problematic_code
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def simulate_filter_behavior():
    """Simulate how the filter should behave with the fix."""
    
    print("\n🧪 Filter Behavior Simulation")
    print("-" * 40)
    
    # Simulate the data we have
    test_data = [
        {"title": "Course 1", "url_status": "Working"},
        {"title": "Course 2", "url_status": "Not Working"},
        {"title": "Course 3", "url_status": "Working"},
        {"title": "Course 4", "url_status": "unchecked"},
        {"title": "Course 5", "url_status": "Working"},
    ]
    
    # Simulate filtering by "Working"
    filter_value = "Working"
    
    print(f"Filter Selection: '{filter_value}'")
    print("Expected Results (courses with exactly 'Working' status):")
    
    matching_courses = []
    for course in test_data:
        # Simulate the new exact matching logic
        if course["url_status"].strip().lower() == filter_value.lower():
            matching_courses.append(course)
            print(f"   ✅ {course['title']} (Status: {course['url_status']})")
    
    print(f"\nTotal matching courses: {len(matching_courses)}")
    
    # Show what would have matched with the old logic (problematic)
    print("\nOld Logic Would Have Matched (WRONG):")
    for course in test_data:
        if filter_value.lower() in course["url_status"].lower():
            if course not in matching_courses:
                print(f"   ❌ {course['title']} (Status: {course['url_status']}) - FALSE POSITIVE")
    
    return True

def main():
    """Main test function."""
    
    print("URL Status Filter - Exact Matching Fix Validation")
    print("=" * 55)
    
    test1 = test_url_status_exact_matching()
    test2 = simulate_filter_behavior()
    
    print("\n" + "=" * 55)
    
    if test1 and test2:
        print("🎉 FIX VALIDATION SUCCESSFUL!")
        print("\n✅ Problem Resolved:")
        print("   • Changed from partial matching (includes) to exact matching (===)")
        print("   • Filtering by 'Working' now only shows 'Working' courses")
        print("   • Filtering by 'Not Working' now only shows 'Not Working' courses")
        print("   • Fixed in both filter function instances")
        
        print("\n🔧 Technical Changes:")
        print("   • OLD: urlStatus.includes(urlStatusFilter)")
        print("   • NEW: urlStatus.trim().toLowerCase() === urlStatusFilter.toLowerCase()")
        
        print("\n🚀 Ready to Test:")
        print("   1. Go to Admin → Manage Courses")
        print("   2. Select 'Working' from URL Status filter")
        print("   3. Should only show courses with 'Working' status")
        print("   4. Select 'Not Working' to verify it works independently")
        
        return True
    else:
        print("❌ FIX VALIDATION FAILED")
        print("The URL Status filter fix needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
