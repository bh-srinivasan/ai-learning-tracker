"""
Debug script to test the upload endpoint and identify why it's returning HTML instead of JSON
"""

import requests
import os

def test_upload_endpoint():
    """Test the upload endpoint directly to see what's happening"""
    
    # Check if test file exists
    test_file = "test_upload_fix.xlsx"
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        print("Run test_upload_fix.py first to create the test file")
        return
    
    print(f"🧪 Testing upload endpoint with {test_file}")
    
    # Test the endpoint
    url = "http://localhost:5000/admin/upload_excel_courses"
    
    try:
        # Create multipart form data
        with open(test_file, 'rb') as f:
            files = {'excel_file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"📡 Making POST request to {url}")
            response = requests.post(url, files=files)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            print(f"📊 Response Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            # Check if response is HTML or JSON
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                print("✅ Response is JSON:")
                try:
                    json_data = response.json()
                    print(f"   {json_data}")
                except Exception as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Raw response: {response.text[:500]}")
            else:
                print("❌ Response is NOT JSON (this is the problem!):")
                print(f"Content-Type: {content_type}")
                print("First 500 characters of response:")
                print(response.text[:500])
                
                # Check for common error patterns
                if "<!DOCTYPE" in response.text:
                    print("\n🔍 Response is HTML - likely an error page or redirect")
                if "login" in response.text.lower():
                    print("🔍 Response contains 'login' - likely authentication issue")
                if "404" in response.text:
                    print("🔍 Response contains '404' - endpoint not found")
                if "500" in response.text:
                    print("🔍 Response contains '500' - internal server error")
                    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the Flask app running?")
        print("Try running: python app.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_server_status():
    """Test if the server is running and accessible"""
    try:
        response = requests.get("http://localhost:5000/")
        print(f"✅ Server is running (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Upload Endpoint Debug Tool")
    print("=" * 50)
    
    # First check if server is running
    if test_server_status():
        print("\n🧪 Testing upload endpoint...")
        test_upload_endpoint()
    else:
        print("\n💡 Start the Flask app first:")
        print("   python app.py")
        print("Then run this debug script again.")
