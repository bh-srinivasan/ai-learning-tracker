#!/usr/bin/env python3
"""
Real-time debugging script to check what the filter is actually receiving.
This will help us understand why the filter still isn't working.
"""

import sqlite3
import re

def debug_actual_implementation():
    """Debug the actual filter implementation."""
    
    print("🔍 Real-time URL Status Filter Debug")
    print("=" * 50)
    
    # Check what we actually have in the database
    conn = sqlite3.connect('ai_learning.db')
    cursor = conn.cursor()
    
    print("📊 Database Reality Check:")
    cursor.execute("SELECT id, title, url_status FROM courses WHERE url_status IS NOT NULL ORDER BY url_status")
    courses = cursor.fetchall()
    
    status_counts = {}
    for course_id, title, status in courses:
        status_counts[status] = status_counts.get(status, 0) + 1
        if status_counts[status] <= 2:  # Show first 2 of each type
            print(f"   ID {course_id}: '{status}' - {title[:40]}...")
    
    print(f"\n📈 Status Summary:")
    for status, count in status_counts.items():
        print(f"   '{status}': {count} courses")
    
    conn.close()
    
    # Check the actual HTML template structure
    template_path = 'templates/admin/courses.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n🔍 Template Analysis:")
    
    # Check dropdown values
    dropdown_pattern = r'<option value="([^"]*)"[^>]*>.*?</option>'
    dropdown_matches = re.findall(dropdown_pattern, content)
    
    print("   Dropdown Values:")
    for value in dropdown_matches:
        if value and value != "":  # Skip empty values
            print(f"     '{value}'")
    
    # Check if we have the correct filter logic
    filter_patterns = [
        ("URL Status Cell Extraction", r"urlStatusCell = cells\[5\]"),
        ("Text Content Processing", r"statusText = urlStatusCell\.textContent\.trim\(\)"),
        ("Space Removal", r"replace\(/\^\\\s\*/, \"\"\)"),
        ("Exact Matching", r"urlStatus === urlStatusFilter\.toLowerCase\(\)"),
    ]
    
    print("\n   Filter Logic Check:")
    for name, pattern in filter_patterns:
        if re.search(pattern, content):
            print(f"     ✅ {name}")
        else:
            print(f"     ❌ {name}")
    
    return True

def create_browser_debug_script():
    """Create a JavaScript debug script that can be run in browser console."""
    
    debug_js = """
// URL Status Filter Debug Script
// Run this in browser console on the Manage Courses page

console.log("🔍 URL Status Filter Debug");
console.log("=".repeat(40));

// Check if elements exist
const table = document.getElementById('coursesTable');
const urlStatusFilter = document.getElementById('urlStatusFilter');

if (!table) {
    console.error("❌ Table not found!");
    return;
}

if (!urlStatusFilter) {
    console.error("❌ URL Status filter not found!");
    return;
}

console.log("✅ Elements found");

// Get all rows and check URL status column content
const rows = table.querySelectorAll('tbody tr');
console.log(`📊 Found ${rows.length} rows`);

console.log("\\n🔍 URL Status Column Analysis:");
rows.forEach((row, index) => {
    if (index < 5) { // Check first 5 rows
        const cells = row.querySelectorAll('td');
        if (cells[5]) {
            const rawText = cells[5].textContent;
            const trimmedText = rawText.trim();
            const cleanedText = trimmedText.replace(/^\\s*/, "");
            
            console.log(`Row ${index + 1}:`);
            console.log(`  Raw: "${rawText}"`);
            console.log(`  Trimmed: "${trimmedText}"`);
            console.log(`  Cleaned: "${cleanedText}"`);
            console.log(`  Lowercase: "${cleanedText.toLowerCase()}"`);
        }
    }
});

// Test filter function manually
console.log("\\n🧪 Manual Filter Test:");
const testFilter = (filterValue) => {
    console.log(`\\nTesting filter: "${filterValue}"`);
    let matchCount = 0;
    
    rows.forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells[5]) {
            const urlStatusCell = cells[5];
            const statusText = urlStatusCell.textContent.trim();
            const urlStatus = statusText.replace(/^\\s*/, "").toLowerCase();
            
            const matches = urlStatus === filterValue.toLowerCase();
            if (matches) {
                matchCount++;
                if (matchCount <= 3) { // Show first 3 matches
                    console.log(`  ✅ Match ${matchCount}: "${urlStatus}"`);
                }
            }
        }
    });
    
    console.log(`  📊 Total matches: ${matchCount}`);
    return matchCount;
};

// Test each filter value
testFilter("Working");
testFilter("Not Working");
testFilter("Broken");
testFilter("unchecked");

console.log("\\n📋 Debug complete. Check results above.");
"""
    
    print("\n🛠️ Browser Debug Script:")
    print("Copy and paste this into your browser console on the Manage Courses page:")
    print("-" * 50)
    print(debug_js)
    print("-" * 50)
    
    # Also save to file
    with open('browser_debug.js', 'w') as f:
        f.write(debug_js)
    
    print("✅ Debug script saved to 'browser_debug.js'")

def main():
    """Main debug function."""
    
    print("URL Status Filter - Real-time Debugging")
    print("=" * 50)
    
    debug_actual_implementation()
    create_browser_debug_script()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Open Admin → Manage Courses in your browser")
    print("2. Open browser console (F12)")
    print("3. Run the debug script above")
    print("4. Check what the actual text content looks like")
    print("5. Test the filter manually to see what's happening")
    
    return True

if __name__ == "__main__":
    main()
