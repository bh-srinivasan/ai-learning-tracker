#!/usr/bin/env python3
"""
Test script for the enhanced Excel upload functionality with user-friendly error descriptions
"""

import os
import sys
import subprocess
import requests
import pandas as pd
from io import BytesIO

def test_enhanced_upload():
    """Test the enhanced upload functionality"""
    
    print("🧪 Testing Enhanced Excel Upload with Error Descriptions")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5000/admin', timeout=5)
        print("✅ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the Flask app first.")
        return False
    
    # Test 1: No file upload
    print("\n📋 Test 1: No file upload")
    try:
        response = requests.post('http://localhost:5000/admin/upload_excel_courses_enhanced', 
                               files={}, timeout=10)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success', 'N/A')}")
        print(f"Error: {data.get('error', 'N/A')}")
        print(f"Error Description: {data.get('error_description', 'N/A')}")
        assert response.status_code == 400
        assert 'error_description' in data
        print("✅ Test 1 passed")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Invalid file format
    print("\n📋 Test 2: Invalid file format")
    try:
        # Create a text file
        invalid_content = "This is not an Excel file"
        response = requests.post('http://localhost:5000/admin/upload_excel_courses_enhanced',
                               files={'excel_file': ('test.txt', invalid_content, 'text/plain')},
                               timeout=10)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success', 'N/A')}")
        print(f"Error: {data.get('error', 'N/A')}")
        print(f"Error Description: {data.get('error_description', 'N/A')}")
        assert response.status_code == 400
        assert 'error_description' in data
        print("✅ Test 2 passed")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Valid Excel file with missing columns
    print("\n📋 Test 3: Missing required columns")
    try:
        # Create Excel with missing columns
        df = pd.DataFrame({
            'title': ['Test Course'],
            'description': ['Test Description']
            # Missing: url, source, level
        })
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        response = requests.post('http://localhost:5000/admin/upload_excel_courses_enhanced',
                               files={'excel_file': ('test_missing_cols.xlsx', excel_buffer.getvalue(), 
                                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
                               timeout=10)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success', 'N/A')}")
        print(f"Error: {data.get('error', 'N/A')}")
        print(f"Error Description: {data.get('error_description', 'N/A')}")
        assert response.status_code == 400
        assert 'error_description' in data
        print("✅ Test 3 passed")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    # Test 4: Valid Excel file with correct format
    print("\n📋 Test 4: Valid Excel file")
    try:
        # Create valid Excel file
        df = pd.DataFrame({
            'title': ['Enhanced Test Course'],
            'url': ['https://example.com/enhanced-test'],
            'source': ['Test Platform'],
            'level': ['Beginner'],
            'description': ['Test course for enhanced upload'],
            'category': ['Testing'],
            'points': [10]
        })
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        response = requests.post('http://localhost:5000/admin/upload_excel_courses_enhanced',
                               files={'excel_file': ('test_valid.xlsx', excel_buffer.getvalue(), 
                                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
                               timeout=10)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success', 'N/A')}")
        print(f"Message: {data.get('message', 'N/A')}")
        print(f"Success Description: {data.get('success_description', 'N/A')}")
        if 'stats' in data:
            stats = data['stats']
            print(f"Stats: Processed: {stats.get('total_processed', 0)}, Added: {stats.get('added', 0)}, Skipped: {stats.get('skipped', 0)}, Errors: {stats.get('errors', 0)}")
        assert response.status_code == 200
        assert data.get('success') == True
        assert 'success_description' in data
        print("✅ Test 4 passed")
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
    
    print("\n🎉 Enhanced upload testing completed!")
    return True

if __name__ == '__main__':
    test_enhanced_upload()
