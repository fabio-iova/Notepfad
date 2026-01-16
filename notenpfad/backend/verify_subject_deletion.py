import requests

API_URL = "http://localhost:8000"

def test_subject_deletion():
    # 1. Create Subject
    print("Creating subject...")
    res = requests.post(f"{API_URL}/subjects/", json={"name": "DeleteMe", "weighting": 1.0})
    if res.status_code != 200:
        print(f"Failed to create subject: {res.text}")
        return
    subject = res.json()
    subject_id = subject['id']
    print(f"Subject created: {subject_id}")

    # 2. Add Grade
    print("Adding grade...")
    res = requests.post(f"{API_URL}/grades/", json={
        "value": 5.0,
        "type": "Prüfung",
        "subject_id": subject_id,
        "date": "2023-01-01"
    })
    grade = res.json()
    print(f"Grade added: {grade['id']}")

    # 3. Delete Subject
    print("Deleting subject...")
    res = requests.delete(f"{API_URL}/subjects/{subject_id}")
    assert res.status_code == 200
    print("Subject deleted.")

    # 4. Verify Subject Gone
    res = requests.get(f"{API_URL}/subjects/")
    subjects = res.json()
    assert not any(s['id'] == subject_id for s in subjects)
    print("Verified subject is gone.")

    # 5. Verify Grade Gone
    res = requests.get(f"{API_URL}/grades/")
    grades = res.json()
    assert not any(g['subject_id'] == subject_id for g in grades)
    print("Verified grades are gone.")
    print("TEST PASSED")

if __name__ == "__main__":
    try:
        test_subject_deletion()
    except Exception as e:
        print(f"TEST FAILED: {e}")
