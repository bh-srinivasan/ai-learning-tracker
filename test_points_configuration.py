#!/usr/bin/env python3
"""
Test script for Points Configuration update functionality in Admin Settings
"""

import requests
import sqlite3
import sys
import time

# Configuration
BASE_URL = 'http://127.0.0.1:5000'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'
DB_PATH = 'ai_learning.db'

def test_points_configuration():
    """Test the Points Configuration update functionality"""
    
    print("🔧 Testing Points Configuration Update Functionality")
    print("="*60)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Login as admin
        print("1. Logging in as admin...")
        login_data = {
            'username': ADMIN_USERNAME,
            'password': ADMIN_PASSWORD
        }
        
        response = session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=False)
        if response.status_code not in [200, 302]:
            print(f"❌ Login failed with status code: {response.status_code}")
            return False
        
        print("✅ Successfully logged in as admin")
        
        # Step 2: Get current level settings from database
        print("\n2. Getting current level settings from database...")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        current_settings = cursor.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        
        if not current_settings:
            print("❌ No level settings found in database")
            return False
        
        print("Current level settings:")
        for setting in current_settings:
            print(f"  - {setting['level_name']}: {setting['points_required']} points")
        
        # Step 3: Access admin settings page
        print("\n3. Accessing admin settings page...")
        response = session.get(f'{BASE_URL}/admin/settings')
        if response.status_code != 200:
            print(f"❌ Failed to access admin settings page: {response.status_code}")
            return False
        
        print("✅ Successfully accessed admin settings page")
        
        # Step 4: Prepare updated values (increase each by 10)
        print("\n4. Preparing updated values...")
        update_data = {}
        new_values = {}
        
        for setting in current_settings:
            field_name = f"{setting['level_name'].lower()}_points"
            new_value = setting['points_required'] + 10
            update_data[field_name] = str(new_value)
            new_values[setting['level_name']] = new_value
            print(f"  - {setting['level_name']}: {setting['points_required']} → {new_value}")
        
        # Step 5: Submit the update
        print("\n5. Submitting points configuration update...")
        response = session.post(f'{BASE_URL}/admin/settings', data=update_data, allow_redirects=False)
        
        if response.status_code not in [200, 302]:
            print(f"❌ Update failed with status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            return False
        
        print("✅ Update request submitted successfully")
        
        # Step 6: Verify the changes in database
        print("\n6. Verifying changes in database...")
        updated_settings = cursor.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        
        verification_passed = True
        for setting in updated_settings:
            expected_value = new_values[setting['level_name']]
            actual_value = setting['points_required']
            
            if actual_value == expected_value:
                print(f"  ✅ {setting['level_name']}: {actual_value} (correct)")
            else:
                print(f"  ❌ {setting['level_name']}: expected {expected_value}, got {actual_value}")
                verification_passed = False
        
        if not verification_passed:
            print("\n❌ Database verification failed")
            return False
        
        # Step 7: Test with invalid data
        print("\n7. Testing with invalid data...")
        invalid_data = {}
        for setting in current_settings:
            field_name = f"{setting['level_name'].lower()}_points"
            invalid_data[field_name] = "-5"  # Negative value
        
        response = session.post(f'{BASE_URL}/admin/settings', data=invalid_data, allow_redirects=False)
        
        if response.status_code not in [200, 302]:
            print(f"❌ Invalid data test failed with status code: {response.status_code}")
            return False
        
        # Check that values weren't changed to negative
        final_settings = cursor.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        for setting in final_settings:
            if setting['points_required'] < 0:
                print(f"❌ Invalid negative value allowed: {setting['level_name']} = {setting['points_required']}")
                return False
        
        print("✅ Invalid data properly rejected")
        
        # Step 8: Restore original values
        print("\n8. Restoring original values...")
        restore_data = {}
        for setting in current_settings:
            field_name = f"{setting['level_name'].lower()}_points"
            restore_data[field_name] = str(setting['points_required'])
        
        response = session.post(f'{BASE_URL}/admin/settings', data=restore_data, allow_redirects=False)
        
        if response.status_code not in [200, 302]:
            print(f"❌ Restore failed with status code: {response.status_code}")
            return False
        
        # Verify restoration
        restored_settings = cursor.execute('SELECT * FROM level_settings ORDER BY points_required').fetchall()
        
        for original, restored in zip(current_settings, restored_settings):
            if original['points_required'] != restored['points_required']:
                print(f"❌ Restore failed for {original['level_name']}: expected {original['points_required']}, got {restored['points_required']}")
                return False
        
        print("✅ Original values restored successfully")
        
        conn.close()
        
        print("\n" + "="*60)
        print("🎉 ALL POINTS CONFIGURATION TESTS PASSED!")
        print("✅ Login functionality works")
        print("✅ Admin settings page accessible")
        print("✅ Points configuration update works")
        print("✅ Database changes are persisted")
        print("✅ Invalid data is properly rejected")
        print("✅ Values can be restored")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    print("Starting Points Configuration test...")
    print("Make sure the Flask app is running on http://127.0.0.1:5000")
    print("Press Ctrl+C to cancel or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(0)
    
    success = test_points_configuration()
    sys.exit(0 if success else 1)
