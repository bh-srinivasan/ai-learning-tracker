"""
Simple route checker for Azure deployment
"""
import requests

def check_routes():
    base_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    routes_to_test = [
        "/",
        "/login", 
        "/admin",
        "/admin/login",
        "/admin/dashboard",
        "/admin/test-login",
        "/debug/env",
        "/dashboard",
        "/learnings"
    ]
    
    print("=" * 60)
    print("CHECKING AZURE ROUTES")
    print("=" * 60)
    
    for route in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=10, allow_redirects=False)
            
            if response.status_code == 200:
                status = "✅ OK"
            elif response.status_code == 302:
                redirect = response.headers.get('Location', '')
                status = f"🔄 REDIRECT to {redirect}"
            elif response.status_code == 404:
                status = "❌ NOT FOUND"
            elif response.status_code == 500:
                status = "💥 SERVER ERROR"
            else:
                status = f"⚠️  {response.status_code}"
                
            print(f"{route:20}: {status}")
            
        except Exception as e:
            print(f"{route:20}: ❌ ERROR - {e}")

if __name__ == "__main__":
    check_routes()
