#!/usr/bin/env python3
"""
Verify Upload Reports Show Latest Data
"""

import requests

def check_latest_upload_reports():
    """Check that the upload reports show the latest upload data"""
    base_url = "http://127.0.0.1:5000"
    
    # Create session for authentication
    session = requests.Session()
    
    # Login as admin
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    # Get upload reports
    reports_response = session.get(f"{base_url}/admin/reports/")
    
    if reports_response.status_code == 200:
        content = reports_response.text
        
        # Check for our test upload
        if "test_upload.xlsx" in content:
            print("✅ Latest upload (test_upload.xlsx) appears in reports")
            
            # Check for statistics
            if "Total Uploads" in content and "Successful Rows" in content:
                print("✅ Upload statistics are displayed")
            else:
                print("❌ Upload statistics not found")
                
            # Check for detailed data
            if "2025-07-27" in content:  # Today's date
                print("✅ Recent upload timestamp found")
            else:
                print("❌ Recent upload timestamp not found")
                
            print("\n📊 Upload Reports Page Content Analysis:")
            
            # Count upload entries in the table
            import re
            table_rows = re.findall(r'<tr[^>]*>.*?</tr>', content, re.DOTALL)
            data_rows = [row for row in table_rows if 'xlsx' in row or 'xls' in row]
            
            print(f"   Found {len(data_rows)} upload entries in the reports table")
            
            if len(data_rows) > 0:
                print("✅ Upload reports table contains data")
                # Check if the latest upload is at the top
                if "test_upload.xlsx" in data_rows[0]:
                    print("✅ Latest upload appears first in the list")
                else:
                    print("⚠️ Latest upload might not be sorted to the top")
            else:
                print("❌ No upload entries found in reports table")
                
        else:
            print("❌ Latest upload (test_upload.xlsx) not found in reports")
            print("🔍 Checking for any upload data...")
            
            if "excel_upload_reports" in content.lower() or "upload" in content.lower():
                print("ℹ️ Page contains upload-related content")
            else:
                print("❌ Page does not contain expected upload content")
    else:
        print(f"❌ Upload reports page failed: {reports_response.status_code}")

if __name__ == "__main__":
    print("🔍 Verifying Upload Reports Show Latest Data...")
    check_latest_upload_reports()
    print("\n✅ Verification complete!")
