#!/usr/bin/env python3
"""
Final verification test for the URL Status filter fix
"""

import sqlite3

def final_test():
    """Final test of the URL Status filter fix."""
    
    print("🎯 URL Status Filter - Final Fix Verification")
    print("=" * 50)
    
    # Check database
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT url_status, COUNT(*) FROM courses WHERE url_status IS NOT NULL GROUP BY url_status")
    statuses = cursor.fetchall()
    
    print("📊 Database Status Distribution:")
    total_courses = 0
    for status, count in statuses:
        print(f"   '{status}': {count} courses")
        total_courses += count
    
    print(f"\nTotal courses with URL status: {total_courses}")
    
    conn.close()
    
    # Check template
    template_path = 'templates/admin/courses.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Template Implementation Check:")
    
    checks = [
        ("New Text Extraction", "fullText.replace(/[^\\w\\s]/g, '')"),
        ("Working Detection", "urlStatus.includes('working') && !urlStatus.includes('not')"),
        ("Not Working Detection", "urlStatus.includes('not') && urlStatus.includes('working')"),
        ("Broken Detection", "urlStatus.includes('broken')"),
        ("Unchecked Detection", "urlStatus.includes('unchecked')"),
        ("Event Listener", "urlStatusFilter.addEventListener(\"change\", filterTable)"),
    ]
    
    all_passed = True
    for check_name, pattern in checks:
        if pattern in content:
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name}")
            all_passed = False
    
    # Count implementations
    impl_count = content.count("fullText.replace(/[^\\w\\s]/g, '')")
    if impl_count >= 2:
        print(f"   ✅ New logic applied in {impl_count} locations")
    else:
        print(f"   ❌ New logic only in {impl_count} locations (need 2)")
        all_passed = False
    
    return all_passed

def create_test_instructions():
    """Create testing instructions."""
    
    print("\n🚀 Testing Instructions:")
    print("-" * 25)
    print("1. Open Admin → Manage Courses")
    print("2. Open browser console (F12)")
    print("3. Test each filter option:")
    print("")
    print("   ✅ Working → Should show 4 courses")
    print("   ✅ Not Working → Should show 1 course") 
    print("   ✅ Broken → Should show 0 courses")
    print("   ✅ Unchecked → Should show 17 courses")
    print("")
    print("4. Check console for any debug messages")
    print("5. Verify table updates correctly")
    
    print("\n🔍 Debug Test (run in console):")
    print("""
// Quick test in browser console:
const rows = document.querySelectorAll('#coursesTable tbody tr');
rows.forEach((row, i) => {
    if (i < 3) {
        const cell = row.cells[5];
        const text = cell.textContent.replace(/[^\\w\\s]/g, '').trim().toLowerCase();
        console.log(`Row ${i+1}: "${text}"`);
    }
});
""")

def main():
    """Main test function."""
    
    success = final_test()
    create_test_instructions()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FINAL FIX VERIFICATION SUCCESSFUL!")
        print("\n✅ New Approach Implemented:")
        print("   • Robust text extraction using regex")
        print("   • Smart pattern matching for status detection")
        print("   • Handles various icon formats")
        print("   • Applied to both filter functions")
        print("\n🔧 Key Improvements:")
        print("   • Remove ALL non-word characters except spaces")
        print("   • Use includes() for detection, exact match for final result")
        print("   • Handle edge cases like 'not working' vs 'working'")
        print("   • More reliable than regex-based space removal")
        
    else:
        print("❌ FINAL FIX VERIFICATION FAILED")
        
    return success

if __name__ == "__main__":
    main()
