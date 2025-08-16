#!/usr/bin/env python3
"""
Test Upload Reports Integration
"""

import pandas as pd
import requests
import time

def create_test_excel():
    """Create a test Excel file for upload testing"""
    test_data = [
        {
            'title': 'AI Fundamentals Test Course',
            'url': 'https://learn.microsoft.com/ai-fundamentals-test',
            'source': 'Microsoft Learn',
            'level': 'Beginner',
            'description': 'Test course for upload reports',
            'points': 100
        },
        {
            'title': 'Machine Learning Basics Test',
            'url': 'https://learn.microsoft.com/ml-basics-test',
            'source': 'Microsoft Learn',
            'level': 'Intermediate',
            'description': 'Test ML course',
            'points': 150
        },
        {
            'title': 'Invalid Course (missing URL)',
            'url': '',  # This will cause an error
            'source': 'Test Source',
            'level': 'Beginner',
            'description': 'This course has no URL'
        }
    ]
    
    df = pd.DataFrame(test_data)
    df.to_excel('test_upload.xlsx', index=False)
    print("✅ Created test_upload.xlsx with 3 courses (1 valid, 1 valid, 1 invalid)")

def test_upload_with_auth():
    """Test the upload with proper authentication"""
    base_url = "http://127.0.0.1:5000"
    
    # Create session for authentication
    session = requests.Session()
    
    # Login as admin
    print("🔐 Logging in as admin...")
    login_data = {
        'username': 'admin',
        'password': 'YourSecureAdminPassword123!'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    print("✅ Admin login successful")
    
    # Upload the test file
    print("\n📤 Uploading test Excel file...")
    
    with open('test_upload.xlsx', 'rb') as f:
        files = {'excel_file': f}
        upload_response = session.post(f"{base_url}/admin/upload_excel_courses", files=files)
    
    print(f"Upload response status: {upload_response.status_code}")
    
    if upload_response.status_code == 200:
        data = upload_response.json()
        print("✅ Upload completed!")
        print(f"Response: {data}")
        
        if 'stats' in data:
            stats = data['stats']
            print(f"\n📊 Upload Statistics:")
            print(f"   Total processed: {stats.get('total_processed', 0)}")
            print(f"   Successful: {stats.get('successful', 0)}")
            print(f"   Skipped: {stats.get('skipped', 0)}")
            print(f"   Errors: {stats.get('errors', 0)}")
            print(f"   Warnings: {stats.get('warnings', 0)}")
    else:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
    
    # Check upload reports
    print("\n📋 Checking upload reports...")
    reports_response = session.get(f"{base_url}/admin/reports/")
    
    if reports_response.status_code == 200:
        print("✅ Upload reports page accessible")
        if "test_upload.xlsx" in reports_response.text:
            print("✅ Test upload appears in reports")
        else:
            print("❌ Test upload not found in reports")
    else:
        print(f"❌ Upload reports page failed: {reports_response.status_code}")

if __name__ == "__main__":
    print("🧪 Testing Upload Reports Integration...")
    
    # Create test file
    create_test_excel()
    
    # Test upload
    test_upload_with_auth()
    
    # Cleanup
    import os
    try:
        os.remove('test_upload.xlsx')
        print("\n🧹 Cleaned up test file")
    except:
        pass
    
    print("\n✅ Upload reports integration test complete!")
    print("💡 Check the Upload Reports page to verify the upload appears immediately")
