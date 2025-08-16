#!/usr/bin/env python3
"""
Test Excel upload functionality with authentication
"""

import pandas as pd
import os
import sys
import requests

def create_test_excel():
    """Create a test Excel file for upload"""
    test_data = {
        'title': [
            'Test Machine Learning Course',
            'Test Python Course', 
            'Test Azure Course'
        ],
        'description': [
            'A test course about machine learning',
            'A test course about Python programming',
            'A test course about Azure cloud'
        ],
        'url': [
            'https://example.com/ml-course',
            'https://example.com/python-course',
            'https://example.com/azure-course'
        ],
        'source': [
            'Test Learning Platform',
            'Test Learning Platform',
            'Test Learning Platform'
        ],
        'level': [
            'Beginner',
            'Intermediate', 
            'Advanced'
        ],
        'points': [
            100,
            150,
            200
        ],
        'category': [
            'Machine Learning',
            'Programming',
            'Cloud Computing'
        ]
    }
    
    df = pd.DataFrame(test_data)
    excel_file = 'test_excel_upload.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"✅ Created test Excel file: {excel_file}")
    return excel_file

def test_with_authentication():
    """Test the upload with proper authentication"""
    session = requests.Session()
    
    try:
        # Step 1: Get login page to establish session
        print("🔐 Step 1: Getting login page...")
        login_page = session.get('http://localhost:5000/login')
        print(f"   Login page status: {login_page.status_code}")
        
        # Step 2: Login as admin
        print("🔐 Step 2: Logging in as admin...")
        login_data = {
            'username': 'admin',
            'password': os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword123!')
        }
        
        login_response = session.post('http://localhost:5000/login', data=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        # Check if login was successful by looking for redirect or admin content
        if login_response.status_code == 200 and 'dashboard' not in login_response.url.lower():
            print("   ⚠️ Login may have failed - checking response...")
            if 'Invalid username or password' in login_response.text:
                print("   ❌ Login failed - invalid credentials")
                print(f"   Trying with ADMIN_PASSWORD env var: {login_data['password'][:5]}...")
                return False
        else:
            print("   ✅ Login successful!")
        
        # Step 3: Access admin courses page to verify admin access
        print("🔐 Step 3: Verifying admin access...")
        admin_page = session.get('http://localhost:5000/admin/courses')
        print(f"   Admin page status: {admin_page.status_code}")
        
        if admin_page.status_code != 200:
            print(f"   ❌ Cannot access admin page: {admin_page.status_code}")
            return False
        
        # Step 4: Create and upload Excel file
        print("📤 Step 4: Uploading Excel file...")
        excel_file = create_test_excel()
        
        with open(excel_file, 'rb') as f:
            files = {'excel_file': (excel_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            upload_response = session.post(
                'http://localhost:5000/admin/upload_excel_courses',
                files=files,
                timeout=30
            )
            
            print(f"   Upload status: {upload_response.status_code}")
            print(f"   Content type: {upload_response.headers.get('content-type', 'unknown')}")
            
            if upload_response.headers.get('content-type', '').startswith('application/json'):
                result = upload_response.json()
                print(f"   Response: {result}")
                
                if result.get('success'):
                    print("   ✅ Upload successful!")
                    stats = result.get('stats', {})
                    print(f"     - Total processed: {stats.get('total_processed', 0)}")
                    print(f"     - Successfully added: {stats.get('added', 0)}")
                    print(f"     - Skipped (duplicates): {stats.get('skipped', 0)}")
                    print(f"     - Errors: {stats.get('errors', 0)}")
                    
                    if stats.get('error_details'):
                        print("     ⚠️ Error details:")
                        for error in stats['error_details'][:3]:
                            print(f"       - {error}")
                    return True
                else:
                    print(f"   ❌ Upload failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print("   ❌ Unexpected response format (not JSON)")
                print(f"   Response preview: {upload_response.text[:200]}...")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test file
        if 'excel_file' in locals() and os.path.exists(excel_file):
            os.remove(excel_file)
            print(f"🧹 Cleaned up test file: {excel_file}")

def check_admin_password():
    """Check what admin password is set"""
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    if admin_pwd:
        print(f"✅ ADMIN_PASSWORD environment variable found: {admin_pwd[:5]}...")
    else:
        print("⚠️ ADMIN_PASSWORD environment variable not set, using default")
        print("   If login fails, set ADMIN_PASSWORD environment variable")

if __name__ == '__main__':
    print("🧪 Testing Excel Upload with Authentication")
    print("=" * 50)
    
    # Check dependencies
    try:
        import pandas as pd
        import openpyxl
        print(f"✅ pandas version: {pd.__version__}")
        print(f"✅ openpyxl version: {openpyxl.__version__}")
    except ImportError as e:
        print(f"❌ Required libraries not available: {e}")
        sys.exit(1)
    
    # Check admin password
    check_admin_password()
    
    # Test upload with authentication
    success = test_with_authentication()
    
    if success:
        print("\n🎉 Excel upload test completed successfully!")
    else:
        print("\n❌ Excel upload test failed.")
        print("   Common issues:")
        print("   1. Check ADMIN_PASSWORD environment variable")
        print("   2. Ensure Flask app is running on localhost:5000")
        print("   3. Check admin user exists in database")
