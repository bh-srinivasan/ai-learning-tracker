#!/usr/bin/env python3
"""
Test the fixed profile page
"""
import sys
sys.path.append('.')

from app import app
import sqlite3

def test_fixed_profile():
    """Test the fixed profile page"""
    print("TESTING FIXED PROFILE PAGE")
    print("=" * 40)
    
    # Test the Flask application
    with app.test_client() as client:
        print("1. Testing login...")
        
        # Login with bharath/bharath
        response = client.post('/login', data={
            'username': 'bharath',
            'password': 'bharath'
        }, follow_redirects=False)
        
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"   Redirected to: {location}")
            
            if 'dashboard' in location or location.endswith('/'):
                print("   ✅ Login successful")
                
                print("2. Testing profile access...")
                
                # Follow the redirect to ensure session is set
                dashboard_response = client.get(location)
                print(f"   Dashboard access: {dashboard_response.status_code}")
                
                # Now test profile
                profile_response = client.get('/profile')
                
                print(f"   Profile status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    content = profile_response.data.decode('utf-8')
                    
                    # Check for success indicators
                    success_indicators = [
                        'My Profile',
                        'bharath',
                        'Level',
                        'Points',
                        'Learning Stats'
                    ]
                    
                    found = []
                    for indicator in success_indicators:
                        if indicator in content:
                            found.append(indicator)
                    
                    if len(found) >= 3:
                        print(f"   ✅ SUCCESS: Profile loaded with {len(found)}/5 expected elements")
                        print(f"   Found: {found}")
                        print(f"   Content length: {len(content)} characters")
                        
                        # Check for error indicators
                        error_indicators = ['Internal Server Error', 'Traceback', '500', 'Exception']
                        errors_found = [err for err in error_indicators if err in content]
                        
                        if errors_found:
                            print(f"   ⚠️  Errors detected: {errors_found}")
                        else:
                            print("   ✅ No errors detected in profile page")
                        
                    else:
                        print(f"   ⚠️  Profile loaded but missing elements. Found: {found}")
                        
                elif profile_response.status_code == 302:
                    print(f"   🔄 Profile redirected to: {profile_response.headers.get('Location')}")
                elif profile_response.status_code == 500:
                    print("   ❌ Internal Server Error still present")
                    content = profile_response.data.decode('utf-8')
                    print("   Error preview:")
                    print(content[:500])
                else:
                    print(f"   ❌ Unexpected status: {profile_response.status_code}")
                    
            else:
                print(f"   ❌ Login failed - wrong redirect: {location}")
        else:
            print(f"   ❌ Login failed with status: {response.status_code}")

def test_profile_post_functionality():
    """Test profile POST functionality (profile updates)"""
    print("\n3. Testing profile update functionality...")
    print("-" * 40)
    
    with app.test_client() as client:
        # Login first
        login_response = client.post('/login', data={
            'username': 'bharath',
            'password': 'bharath'
        })
        
        if login_response.status_code == 302:
            # Test profile update
            update_response = client.post('/profile', data={
                'user_selected_level': 'Intermediate'
            }, follow_redirects=True)
            
            print(f"   Profile update status: {update_response.status_code}")
            
            if update_response.status_code == 200:
                content = update_response.data.decode('utf-8')
                
                if 'Profile updated successfully' in content or 'Intermediate' in content:
                    print("   ✅ Profile update appears successful")
                else:
                    print("   ⚠️  Profile update status unclear")
            else:
                print(f"   ❌ Profile update failed: {update_response.status_code}")

if __name__ == "__main__":
    test_fixed_profile()
    test_profile_post_functionality()
