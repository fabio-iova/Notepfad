
import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req = urllib.request.Request(url, method=method, headers=headers)
    if data:
        req.data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}")
        return None, None

def test_login():
    print("Testing Login...")
    
    # 1. Test Incorrect password
    status, _ = make_request(f"{BASE_URL}/login", "POST", {"username": "admin", "password": "123"})
    if status is None:
        print("❌ Cannot connect to server.")
        return None
        
    if status == 401:
        print("✅ Incorrect login rejected (401)")
    else:
        print(f"❌ Expected 401, got {status}")

    # 2. Test Correct password
    status, data = make_request(f"{BASE_URL}/login", "POST", {"username": "admin", "password": "1234"})
    if status == 200:
        if "access_token" in data:
            print("✅ Login successful, token received")
            return data["access_token"]
        else:
            print("❌ No access token in response")
            return None
    else:
        print(f"❌ Login failed: {status}")
        return None

def test_protected_route(token):
    print("\nTesting Protected Route (/subjects/)...")
    
    # 1. Without Token
    status, _ = make_request(f"{BASE_URL}/subjects/", "GET")
    if status == 401:
        print("✅ Unauthorized access blocked (401)")
    else:
        print(f"❌ Access without token should be 401, but got {status}")

    # 2. With Token
    headers = {"Authorization": f"Bearer {token}"}
    status, data = make_request(f"{BASE_URL}/subjects/", "GET", headers=headers)
    if status == 200:
        print("✅ Authorized access successful (200)")
        print(f"   Found {len(data)} subjects")
    else:
        print(f"❌ Access with token failed: {status}")

if __name__ == "__main__":
    token = test_login()
    if token:
        test_protected_route(token)
