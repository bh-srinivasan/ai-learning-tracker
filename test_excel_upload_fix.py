#!/usr/bin/env python3
"""
Test Excel upload functionality with a simple test file
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

def test_upload_endpoint():
    """Test the upload endpoint directly"""
    try:
        # Create test Excel file
        excel_file = create_test_excel()
        
        # Test if server is running
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            print(f"✅ Server is running - Health check: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Server not running or not accessible: {e}")
            print("Please start the Flask app first: python app.py")
            return
        
        # Prepare file upload
        with open(excel_file, 'rb') as f:
            files = {'excel_file': (excel_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            # Make the upload request
            print(f"📤 Uploading {excel_file} to /admin/upload_excel_courses...")
            response = requests.post(
                'http://localhost:5000/admin/upload_excel_courses',
                files=files,
                timeout=30
            )
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                print(f"📥 Response JSON: {result}")
                
                if result.get('success'):
                    print("✅ Upload successful!")
                    stats = result.get('stats', {})
                    print(f"   - Total processed: {stats.get('total_processed', 0)}")
                    print(f"   - Successfully added: {stats.get('added', 0)}")
                    print(f"   - Skipped (duplicates): {stats.get('skipped', 0)}")
                    print(f"   - Errors: {stats.get('errors', 0)}")
                    
                    if stats.get('error_details'):
                        print("⚠️ Error details:")
                        for error in stats['error_details'][:5]:  # Show first 5 errors
                            print(f"   - {error}")
                else:
                    print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"📥 Response Text: {response.text[:500]}...")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test file
        if os.path.exists(excel_file):
            os.remove(excel_file)
            print(f"🧹 Cleaned up test file: {excel_file}")

def check_pandas_openpyxl():
    """Check if required libraries are available"""
    try:
        import pandas as pd
        print(f"✅ pandas version: {pd.__version__}")
    except ImportError as e:
        print(f"❌ pandas not available: {e}")
        return False
        
    try:
        import openpyxl
        print(f"✅ openpyxl version: {openpyxl.__version__}")
    except ImportError as e:
        print(f"❌ openpyxl not available: {e}")
        return False
        
    return True

if __name__ == '__main__':
    print("🧪 Testing Excel Upload Functionality")
    print("=" * 50)
    
    # Check dependencies
    if not check_pandas_openpyxl():
        print("❌ Required libraries not available")
        sys.exit(1)
    
    # Test upload
    test_upload_endpoint()
