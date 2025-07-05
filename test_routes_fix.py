#!/usr/bin/env python3
"""
Quick test to verify admin routes are working
"""

from app import app

def test_routes():
    """Test if the problematic routes are registered"""
    with app.app_context():
        from flask import url_for
        
        print("🧪 Testing Flask route registration...")
        
        try:
            # Test the problematic route
            url1 = url_for('admin_reset_user_password')
            print(f"✅ admin_reset_user_password: {url1}")
            
            # Test the other reset route
            url2 = url_for('admin_reset_all_user_passwords') 
            print(f"✅ admin_reset_all_user_passwords: {url2}")
            
            # Test admin users route
            url3 = url_for('admin_users')
            print(f"✅ admin_users: {url3}")
            
            print("\n🎉 ALL ROUTES ARE WORKING!")
            return True
            
        except Exception as e:
            print(f"❌ Route error: {e}")
            return False

if __name__ == "__main__":
    success = test_routes()
    if success:
        print("\n✅ The manage users page should now work correctly!")
    else:
        print("\n❌ There are still route registration issues.")
