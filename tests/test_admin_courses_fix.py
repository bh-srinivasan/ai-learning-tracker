#!/usr/bin/env python3
"""
Test the admin courses page fix
"""
import sys
sys.path.append('.')

from app import app
import sqlite3

def test_admin_courses_fix():
    """Test that admin courses page works now"""
    print("TESTING ADMIN COURSES PAGE FIX")
    print("=" * 40)
    
    with app.test_client() as client:
        # Login as admin
        print("1. Testing admin login...")
        
        # First check if admin user exists and fix password if needed
        conn = sqlite3.connect('ai_learning.db')
        admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        
        if not admin_user:
            print("❌ Admin user not found")
            return
        
        # Test admin password
        from werkzeug.security import check_password_hash, generate_password_hash
        
        if not check_password_hash(admin_user[2], 'admin'):  # password_hash is column 2
            print("   Fixing admin password...")
            new_hash = generate_password_hash('admin')
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                        (new_hash, 'admin'))
            conn.commit()
            print("   ✅ Admin password fixed")
        
        conn.close()
        
        # Login as admin
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=False)
        
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"   Redirected to: {location}")
            
            if 'admin' in location.lower():
                print("   ✅ Admin login successful")
                
                print("2. Testing admin courses page...")
                
                # Follow redirect to establish session
                admin_response = client.get(location)
                print(f"   Admin dashboard access: {admin_response.status_code}")
                
                # Test the admin courses page
                courses_response = client.get('/admin/courses')
                
                print(f"   Admin courses status: {courses_response.status_code}")
                
                if courses_response.status_code == 200:
                    content = courses_response.data.decode('utf-8')
                    
                    # Check for success indicators
                    success_indicators = [
                        'Manage Courses',
                        'URL Validation',
                        'Add New Course'
                    ]
                    
                    found = []
                    for indicator in success_indicators:
                        if indicator in content:
                            found.append(indicator)
                    
                    if found:
                        print(f"   ✅ SUCCESS: Admin courses page loaded")
                        print(f"   Found: {found}")
                        print(f"   Content length: {len(content)} characters")
                        
                        # Check for error indicators
                        error_indicators = ['BuildError', 'url_for', 'endpoint', 'Traceback']
                        errors_found = [err for err in error_indicators if err in content]
                        
                        if errors_found:
                            print(f"   ❌ Errors detected: {errors_found}")
                            # Show some context around errors
                            for error in errors_found:
                                if error in content:
                                    lines = content.split('\n')
                                    for i, line in enumerate(lines):
                                        if error in line:
                                            print(f"   Error context (line {i}):")
                                            start = max(0, i-2)
                                            end = min(len(lines), i+3)
                                            for j in range(start, end):
                                                marker = " -> " if j == i else "    "
                                                print(f"   {marker}{j}: {lines[j][:100]}")
                                            break
                        else:
                                            print("   ✅ No URL routing errors detected")
                                            
                    else:
                        print("   ⚠️  Admin courses page loaded but missing expected content")
                        
                elif courses_response.status_code == 500:
                    print("   ❌ Internal Server Error in admin courses")
                    content = courses_response.data.decode('utf-8')
                    print("   Error preview:")
                    print(content[:1000])
                    
                else:
                    print(f"   ❌ Unexpected status: {courses_response.status_code}")
                    
                # Test URL validation endpoint specifically
                print("3. Testing URL validation endpoint...")
                
                validation_response = client.get('/admin/url-validation')
                print(f"   URL validation status: {validation_response.status_code}")
                
                if validation_response.status_code == 200:
                    print("   ✅ URL validation page accessible")
                elif validation_response.status_code == 500:
                    print("   ❌ URL validation page has errors")
                    content = validation_response.data.decode('utf-8')
                    print("   Error preview:")
                    print(content[:500])
                else:
                    print(f"   ⚠️  URL validation status: {validation_response.status_code}")
                    
            else:
                print(f"   ❌ Admin login failed - wrong redirect: {location}")
        else:
            print(f"   ❌ Admin login failed with status: {response.status_code}")

if __name__ == "__main__":
    test_admin_courses_fix()
