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
    subjects = req("/subjects/")
    for s in subjects:
        if s['name'] == name:
            return s
    return req("/subjects/", "POST", {"name": name, "weighting": 1.0})

def run_test():
    print("--- Starting Deletion Verification ---")
    
    # 1. Ensure a subject exists
    s_test = get_or_create_subject("DeletionTest")
    
    # 2. Add a grade
    grade = req("/grades/", "POST", {
        "value": 4.5, 
        "subject_id": s_test['id'], 
        "type": "Exam", 
        "date": "2023-05-01"
    })
    grade_id = grade['id']
    print(f"Created Grade ID {grade_id}")
    
    # 3. Verify it exists
    all_grades = req("/grades/")
    if not any(g['id'] == grade_id for g in all_grades):
        raise Exception("Grade not found after creation")
    print("Grade verified in list.")
    
    # 4. Delete it
    req(f"/grades/{grade_id}", "DELETE")
    print("Delete request sent.")
    
    # 5. Verify it is gone
    all_grades_after = req("/grades/")
    if any(g['id'] == grade_id for g in all_grades_after):
        raise Exception("Grade still exists after deletion!")
        
    print("✅ Deletion Verification PASSED")

if __name__ == "__main__":
    run_test()
