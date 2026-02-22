from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, models
from database import Base
import os

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_guest.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module():
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_guest.db"):
        os.remove("./test_guest.db")

def test_guest_login_flow():
    # 1. Guest Login
    response = client.post("/guest-login")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "parent"
    assert data["username"].startswith("guest_")
    
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Check Subjects (Seeded)
    response = client.get("/subjects/", headers=headers)
    assert response.status_code == 200
    subjects = response.json()
    names = [s["name"] for s in subjects]
    assert "Mathematik" in names
    assert "Deutsch" in names
    
    # 3. Check Grades (Seeded)
    # Find student ID (should be seeded)
    # Get children first to find student ID
    user_id = data["user_id"]
    response = client.get(f"/users/{user_id}/children", headers=headers)
    assert response.status_code == 200
    children = response.json()
    assert len(children) >= 1
    
    student_user_id = children[0]["id"]
    # Get student profile id... endpoint returns child user with student_profile
    student_profile = children[0]["student_profile"]
    assert student_profile is not None
    student_id = student_profile["id"]
    
    response = client.get(f"/grades/?student_id={student_id}", headers=headers)
    assert response.status_code == 200
    grades = response.json()
    assert len(grades) > 0

    return headers # Return headers for next test if needed

def test_isolation():
    # 1. Create Admin Subject
    # Hack: Creating admin user manually in test db
    db = TestingSessionLocal()
    admin = models.User(username="admin_test", password_hash="hash", role="parent")
    db.add(admin)
    db.commit()
    
    admin_sub = models.Subject(name="AdminSecretSubject", owner_id=admin.id)
    db.add(admin_sub)
    db.commit()
    db.close()
    
    # 2. Guest Login
    response = client.post("/guest-login")
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Verify Guest DOES NOT see Admin Subject
    response = client.get("/subjects/", headers=headers)
    subjects = response.json()
    names = [s["name"] for s in subjects]
    
    assert "AdminSecretSubject" not in names
    assert "Mathematik" in names # Guest's own subject

    print("Isolation Verified: Guest cannot see Admin's subject.")

if __name__ == "__main__":
    setup_module()
    try:
        test_guest_login_flow()
        test_isolation()
        print("✅ All Guest Mode tests passed!")
    finally:
        teardown_module()
