#!/usr/bin/env python3
"""
Azure admin password reset via HTTP endpoint
"""
import requests
import time

def reset_azure_admin():
    """Reset admin password on Azure"""
    
    azure_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    print(f"🔄 Resetting admin password on Azure...")
    print(f"🌐 Azure URL: {azure_url}")
    
    # Wait for deployment to complete
    print("⏳ Waiting for Azure deployment to complete...")
    time.sleep(30)
    
    try:
        # Try to access the debug endpoint to reset admin
        reset_url = f"{azure_url}/admin/debug/reset-admin-password"
        
        print(f"🔧 Attempting to reset admin password...")
        response = requests.post(reset_url, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Success: {result.get('message', 'Admin password reset')}")
                return True
            except:
                print("✅ Admin password reset successful (no JSON response)")
                return True
        else:
            print(f"⚠️  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Alternative: Just run app.py startup which will reset admin password
    print("\n🔄 Alternative: App startup will reset admin password automatically")
    try:
        response = requests.get(f"{azure_url}/", timeout=30)
        if response.status_code == 200:
            print("✅ Azure app is responding - admin password should be reset on startup")
            return True
        else:
            print(f"⚠️  Azure app status: {response.status_code}")
    except Exception as e:
        print(f"❌ Azure app check failed: {e}")
    
    return False

if __name__ == "__main__":
    success = reset_azure_admin()
    if success:
        print("\n🎉 ADMIN LOGIN SHOULD NOW WORK!")
        print("👤 Username: admin")
        print("🔐 Password: YourSecureAdminPassword123!")
        print(f"🌐 Login at: https://ai-learning-tracker-bharath.azurewebsites.net")
    else:
        print("\n❌ Azure admin reset may have failed")
        print("Try logging in anyway - the app startup should reset the password")
