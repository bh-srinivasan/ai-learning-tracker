// URL Status Filter Debug - Run this in browser console
console.log("🔍 URL Status Filter Debug - Step by Step");

// Step 1: Check if elements exist
const urlStatusFilter = document.getElementById('urlStatusFilter');
const table = document.getElementById('coursesTable');

if (!urlStatusFilter) {
    console.error("❌ urlStatusFilter element not found!");
} else {
    console.log("✅ urlStatusFilter found");
}

if (!table) {
    console.error("❌ coursesTable not found!");
} else {
    console.log("✅ coursesTable found");
    console.log(`📊 Table has ${table.querySelectorAll('tbody tr').length} rows`);
}

// Step 2: Test manual filtering
function testManualFilter(filterValue) {
    console.log(`\n🧪 Testing filter: "${filterValue}"`);
    
    const rows = table.querySelectorAll('tbody tr');
    let matches = 0;
    
    rows.forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells[5]) {
            const urlStatusCell = cells[5];
            const statusText = urlStatusCell.textContent.trim();
            const urlStatus = statusText.replace(/^\s*/, "").toLowerCase();
            
            const isMatch = urlStatus === filterValue.toLowerCase();
            
            if (index < 3) { // Show first 3 for debugging
                console.log(`  Row ${index + 1}: "${statusText}" → "${urlStatus}" → Match: ${isMatch}`);
            }
            
            if (isMatch) matches++;
        }
    });
    
    console.log(`  📊 Total matches: ${matches}`);
    return matches;
}

// Step 3: Test all filter values
testManualFilter("Working");
testManualFilter("Not Working");
testManualFilter("Broken");
testManualFilter("unchecked");

// Step 4: Test the actual filter function
console.log("\n🔧 Testing actual filter function:");
urlStatusFilter.value = "Working";
filterTable(); // This should be defined in the page

console.log("\n📋 Debug complete. Check results above.");
