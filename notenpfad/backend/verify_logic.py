import json
import urllib.request
import urllib.parse
import time

BASE_URL = "http://localhost:8000"

def req(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        if hasattr(e, 'read'):
            print(f"Error Body: {e.read().decode()}")
        print(f"Request failed: {url} {e}")
        raise

def get_or_create_subject(name):
    # Fetch all subjects
    subjects = req("/subjects/")
    for s in subjects:
        if s['name'] == name:
            return s
    # Create if not found
    return req("/subjects/", "POST", {"name": name, "weighting": 1.0})

def run_test():
    print("--- Starting Verification (Urllib) ---")
    
    # Wait for server
    for i in range(5):
        try:
            req("/status")
            break
        except:
            print("Waiting for server...")
            time.sleep(1)

    # 1. Reset (Clear data)
    req("/reset", "POST")
    print("Reset complete.")

    # 2. Get/Create Subjects
    s_math = get_or_create_subject("Mathematik")
    s_deutsch = get_or_create_subject("Deutsch")
    print(f"Subjects: Math ID={s_math['id']}, Deutsch ID={s_deutsch['id']}")

    # 3. Add Grades
    # Vornote: Math 5.0, Deutsch 5.0 -> Avg 5.0
    req("/grades/", "POST", {"value": 5.0, "subject_id": s_math['id'], "type": "Vornote", "date": "2023-01-01"})
    req("/grades/", "POST", {"value": 5.0, "subject_id": s_deutsch['id'], "type": "Vornote", "date": "2023-01-01"})
    
    # Exam Math: 4.0
    req("/grades/", "POST", {"value": 4.0, "subject_id": s_math['id'], "type": "Prüfung", "date": "2023-02-01"})
    
    # Exam Deutsch: Aufsatz 4.0, Sprachbetrachtung 6.0 -> Avg 5.0 ( (4+6)/2 )
    req("/grades/", "POST", {"value": 4.0, "subject_id": s_deutsch['id'], "type": "Aufsatz", "date": "2023-02-01"})
    req("/grades/", "POST", {"value": 6.0, "subject_id": s_deutsch['id'], "type": "Sprachbetrachtung", "date": "2023-02-01"})

    # 4. Check Average
    # Expected logic:
    # Vornote = (5.0 + 5.0)/2 = 5.0
    # Exam Math = 4.0
    # Exam Deutsch = (4.0 + 6.0)/2 = 5.0
    # Exam Total = (4.0 + 5.0)/2 = 4.5
    # Overall = (5.0 + 4.5)/2 = 4.75
    # Passed = True (>= 4.75)

    res = req("/average/")
    print("Result:", json.dumps(res, indent=2))
    
    # Verify values
    try:
        assert res['average'] == 4.75, f"Expected 4.75, got {res['average']}"
        assert res['passed'] == True, "Expected passed=True"
        
        # Details check
        assert res['details']['vornote']['value'] == 5.0
        assert res['details']['exam']['value'] == 4.5
        assert res['details']['exam']['math'] == 4.0
        assert res['details']['exam']['deutsch']['value'] == 5.0
        
        print("✅ Logic Verification PASSED")
    except AssertionError as e:
        print(f"❌ Logic Verification FAILED: {e}")

if __name__ == "__main__":
    run_test()
