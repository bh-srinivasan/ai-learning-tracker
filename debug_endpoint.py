import requests
import json

# Test what the actual response is
session = requests.Session()

# Login
login_response = session.post("http://localhost:5000/auth/login", data={
    'username': 'admin',
    'password': 'admin'
})

print("Login status:", login_response.status_code)

# Test the endpoint
hash_response = session.post("http://localhost:5000/admin/get-user-hash", data={
    'user_id': '2'
})

print("Hash endpoint status:", hash_response.status_code)
print("Hash endpoint response:", hash_response.text)

# Also test a definitely non-existent endpoint
fake_response = session.post("http://localhost:5000/admin/definitely-not-real")
print("Fake endpoint status:", fake_response.status_code)
