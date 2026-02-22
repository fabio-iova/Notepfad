from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime, timedelta
import bcrypt
import models, database
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError
import openai

models.Base.metadata.create_all(bind=database.engine)



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

import random
import string
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32)) # Random secure fallback
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

app = FastAPI(title="Notenpfad API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")], # Allow all for dev or specific for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str):
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password: str):
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Pydantic Schemas ---

# Basic regex for names/text to prevent HTML/Script tags
# Allows letters (all languages), numbers, spaces, and basic punctuation (-_.,!?)
SAFE_TEXT_REGEX = r'^[\w\s\-\.\,\!\?üöäÜÖÄéèêâàç]+$'

class GradeBase(BaseModel):
    value: float = Field(ge=1.0, le=6.0, description="Grade between 1.0 and 6.0")
    subject_id: int
    type: str = Field("Exam", pattern=SAFE_TEXT_REGEX, max_length=50)
    date: date

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: int
    student_id: int
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str = Field(..., pattern=r'^[a-zA-Z0-9_\-\.]+$', min_length=3, max_length=50, description="Alphanumeric username")

class UserCreate(UserBase):
    password: str = Field(..., min_length=4)

class UserStudentCreate(UserBase):
    password: str = Field(..., min_length=4)

class UserLogin(UserBase):
    password: str

class UserPasswordUpdate(BaseModel):
    password: str = Field(..., min_length=4)

class ChildCreate(UserBase):
    password: str = Field(..., min_length=4)
    name: str = Field(..., pattern=SAFE_TEXT_REGEX, min_length=2, max_length=100)
    parent_id: int

class UserOut(UserBase):
    id: int
    role: str
    student_id: Optional[int] = None
    class Config:
        orm_mode = True

class ChildOut(UserBase):
    id: int
    role: str
    student_profile: Optional['StudentOut'] = None
    class Config:
        orm_mode = True

class StudentOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class SubjectBase(BaseModel):
    name: str = Field(..., pattern=SAFE_TEXT_REGEX, min_length=2, max_length=100)
    weighting: float = Field(1.0, ge=0.0, le=10.0)

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: int
    grades: List[Grade] = []
    class Config:
        orm_mode = True

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    student_id: Optional[int] = None

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Notenpfad API"}

@app.get("/status")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    print("--- STARTUP SEEDING CHECK ---", flush=True)
    try:
        # 1. Create Admin (Parent)
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin:
            print("Creating default admin user...", flush=True)
            admin_pw = os.getenv("ADMIN_PASSWORD", secrets.token_urlsafe(8))
            print(f"Admin Password is: {admin_pw} (SAVE THIS!)", flush=True)
            hashed_password = get_password_hash(admin_pw)
            admin = models.User(username="admin", password_hash=hashed_password, role="parent")
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("✅ Default admin created.", flush=True)
        else:
            print("ℹ️ Admin user already exists.", flush=True)
        
        # 2. Create Sole (Student) linked to Admin
        sole = db.query(models.User).filter(models.User.username == "sole").first()
        if not sole:
            print("Creating default student user: sole...", flush=True)
            sole_pw = os.getenv("STUDENT_PASSWORD", secrets.token_urlsafe(8))
            print(f"Student 'sole' Password is: {sole_pw} (SAVE THIS!)", flush=True)
            hashed_sole_pw = get_password_hash(sole_pw)
            sole = models.User(username="sole", password_hash=hashed_sole_pw, role="student", parent_id=admin.id)
            db.add(sole)
            db.commit()
            db.refresh(sole)
            print("✅ Default student 'sole' created.", flush=True)
        else:
            print("ℹ️ Student 'sole' already exists.", flush=True)

        # 3. Create Student Profile for Sole (if not exists)
        student_profile = db.query(models.Student).filter(models.Student.user_id == sole.id).first()
        if not student_profile:
             print("Creating student profile for sole...", flush=True)
             student_profile = models.Student(name="Sole Iovanna", target_school="Gymnasium", user_id=sole.id)
             db.add(student_profile)
             db.commit()
             print("✅ Student profile for 'sole' created.", flush=True)
        else:
             print("ℹ️ Student profile for 'sole' already exists.", flush=True)

        # 4. Create Default Subjects and Topics
        default_data = {
            "Mathematik": ["Grundoperationen", "Geometrie", "Textaufgaben"],
            "Deutsch": ["Grammatik", "Rechtschreibung", "Textverständnis"]
        }

        for sub_name, topics in default_data.items():
            # Ensure Subject
            # Check if this subject exists for global admin/template usage? 
            # Or just check if *any* exists? 
            # For startup seeding, let's assign them to the admin user we just fetched/created.
            
            subject = db.query(models.Subject).filter(
                models.Subject.name == sub_name, 
                models.Subject.owner_id == admin.id
            ).first()
            
            if not subject:
                print(f"Creating default subject for admin: {sub_name}...", flush=True)
                subject = models.Subject(name=sub_name, weighting=1.0, owner_id=admin.id)
                db.add(subject)
                db.commit()
                db.refresh(subject)
                print(f"✅ Subject '{sub_name}' created.", flush=True)
            else:
                print(f"ℹ️ Subject '{sub_name}' already exists.", flush=True)
            
            # Ensure Topics
            existing_topic_count = db.query(models.Topic).filter(models.Topic.subject_id == subject.id).count()
            if existing_topic_count == 0:
                print(f"Seeding default topics for {sub_name}...", flush=True)
                for topic_name in topics:
                    db.add(models.Topic(name=topic_name, subject_id=subject.id, is_completed=0))
                db.commit()
                print(f"✅ Topics for '{sub_name}' seeded.", flush=True)
            else:
                print(f"ℹ️ Topics for '{sub_name}' already exist ({existing_topic_count}).", flush=True)
        
        print("--- SEEDING COMPLETE ---", flush=True)

    except Exception as e:
        print(f"❌ Error during startup seeding: {e}", flush=True)
        # Don't raise, allow app to start even if seeding fails
    finally:
        db.close()

@app.get("/debug/db-status")
def debug_db_status(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Debug endpoint to check DB content state"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        user_count = db.query(models.User).count()
        student_count = db.query(models.Student).count()
        subject_count = db.query(models.Subject).count()
        grade_count = db.query(models.Grade).count()
        
        admin_exists = db.query(models.User).filter(models.User.username == "admin").first() is not None
        sole_exists = db.query(models.User).filter(models.User.username == "sole").first() is not None
        
        subjects = [s.name for s in db.query(models.Subject).all()]
        
        return {
            "status": "online",
            "counts": {
                "users": user_count,
                "students": student_count,
                "subjects": subject_count,
                "grades": grade_count
            },
            "checks": {
                "admin_exists": admin_exists,
                "sole_exists": sole_exists,
                "subject_names": subjects
            },
            "db_url_masked": str(database.engine.url).split("@")[-1] if "@" in str(database.engine.url) else "..."
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/register", response_model=UserOut)
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.refresh(new_user)
    return new_user

@app.post("/users/student", response_model=UserOut)
@limiter.limit("10/minute")
def create_student(request: Request, user: UserStudentCreate, db: Session = Depends(get_db)):
    # In a real app, we'd check if current_user.role == 'parent'
    # For now, we assume access to this endpoint implies permission (simpler)
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed_password, role="student")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Return role in login response
    # Find linked student_id if applicable
    student_id = None
    if db_user.student_profile:
        student_id = db_user.student_profile.id

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "id": db_user.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id, 
        "username": db_user.username,
        "role": db_user.role,
        "student_id": student_id
    }

def cleanup_old_guests():
    """Background task to delete guest accounts older than 24 hours."""
    db = database.SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        print(f"--- RUNNING GUEST CLEANUP: Deleting guests older than {cutoff} ---")
        
        # Find old guest parents
        old_guests = db.query(models.User).filter(
            models.User.username.like("guest_%"),
            models.User.created_at < cutoff
        ).all()
        
        for guest in old_guests:
            print(f"Cleaning up guest: {guest.username} (Created: {guest.created_at})")
            # 1. Delete associated subjects, topics, and grades
            subjects = db.query(models.Subject).filter(models.Subject.owner_id == guest.id).all()
            for subject in subjects:
                db.query(models.Topic).filter(models.Topic.subject_id == subject.id).delete()
                db.query(models.Grade).filter(models.Grade.subject_id == subject.id).delete()
                db.delete(subject)
            
            # 2. Delete children and their student profiles/grades
            children = db.query(models.User).filter(models.User.parent_id == guest.id).all()
            for child in children:
                student = db.query(models.Student).filter(models.Student.user_id == child.id).first()
                if student:
                    db.query(models.Grade).filter(models.Grade.student_id == student.id).delete()
                    db.delete(student)
                db.delete(child)
            
            # 3. Delete the guest parent
            db.delete(guest)
            
        db.commit()
    except Exception as e:
        print(f"Error during guest cleanup: {e}")
    finally:
        db.close()


@app.post("/guest-login", response_model=Token)
@limiter.limit("3/minute")
def guest_login(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Creates a temporary guest account with seeded data and logs in immediately.
    """
    # Trigger cleanup of old accounts in the background
    background_tasks.add_task(cleanup_old_guests)
    
    # 1. Create unique guest user
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    username = f"guest_{suffix}"
    password = secrets.token_urlsafe(8)
    hashed_password = get_password_hash(password)
    
    guest_parent = models.User(username=username, password_hash=hashed_password, role="parent")
    db.add(guest_parent)
    db.commit()
    db.refresh(guest_parent)
    
    # 2. Create generic child
    child_names = ["Alex", "Leo", "Mia", "Zoé", "Noah", "Luca"]
    child_name = random.choice(child_names) 
    child_username = f"student_{suffix}"
    child_pw = get_password_hash("1234") # Simple pw for them if they need it
    
    guest_child = models.User(username=child_username, password_hash=child_pw, role="student", parent_id=guest_parent.id)
    db.add(guest_child)
    db.commit()
    db.refresh(guest_child)
    
    student_profile = models.Student(name=child_name, target_school="Gymnasium", user_id=guest_child.id)
    db.add(student_profile)
    db.commit()
    db.refresh(student_profile)
    
    # 3. Seed Subjects & Grades (Isolated to this parent)
    # Define Subjects
    subjects_data = {
        "Mathematik": {"weight": 1.0, "topics": ["Grundoperationen", "Geometrie", "Textaufgaben"]},
        "Deutsch": {"weight": 1.0, "topics": ["Grammatik", "Rechtschreibung", "Textverständnis"]}
    }
    
    for sub_name, details in subjects_data.items():
        # Create Subject linked to Parent
        subject = models.Subject(name=sub_name, weighting=details["weight"], owner_id=guest_parent.id)
        db.add(subject)
        db.commit()
        db.refresh(subject)
        
        # Create Topics (Global topics linked to subject, status is currently global per subject id)
        for topic_name in details["topics"]:
             # Random completion
             is_done = random.choice([True, False])
             db.add(models.Topic(name=topic_name, subject_id=subject.id, is_completed=1 if is_done else 0))
        
        # Create Random Grades
        # Add a few grades
        for _ in range(random.randint(2, 4)):
            val = round(random.uniform(3.5, 6.0), 1)
            # 50% chance of 'Prüfung' or 'Vornote'
            g_type = random.choice(["Prüfung", "Vornote", "Test"])
            
            grade = models.Grade(
                value=val,
                subject_id=subject.id,
                student_id=student_profile.id,
                type=g_type,
                date=date.today()
            )
            db.add(grade)
            
    db.commit()
    
    # 4. Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": guest_parent.username, "role": guest_parent.role, "id": guest_parent.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": guest_parent.id,
        "username": guest_parent.username,
        "role": guest_parent.role,
        "student_id": None 
    }

@app.post("/users/children", response_model=UserOut)
@limiter.limit("10/minute")
def create_child(request: Request, child: ChildCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Check parent exists (using current_user for security)
    if current_user.id != child.parent_id and current_user.role != 'admin':
         # Allow admins or the parent themselves
         raise HTTPException(status_code=403, detail="Not authorized to create child for this user")

    parent = db.query(models.User).filter(models.User.id == child.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
        
    # Check username
    if db.query(models.User).filter(models.User.username == child.username).first():
        raise HTTPException(status_code=400, detail="Username taken")
        
    hashed = get_password_hash(child.password)
    new_user = models.User(username=child.username, password_hash=hashed, role="student", parent_id=child.parent_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create Student Profile
    student = models.Student(name=child.name, target_school="Gymnasium", user_id=new_user.id)
    db.add(student)
    db.commit()
    
    return new_user

@app.get("/users/{user_id}/children", response_model=List[ChildOut])
def get_children(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Ensure user can only see their own children
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    children = db.query(models.User).filter(models.User.parent_id == user_id).all()
    return children

@app.delete("/users/children/{child_id}")
def delete_child(child_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Find User
    user = db.query(models.User).filter(models.User.id == child_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Authorize: Only parent can delete their child
    if user.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    # 2. Check if it is a child/student
    if user.role != "student":
        raise HTTPException(status_code=400, detail="Cannot delete non-student user via this endpoint")

    # 3. Find Student Profile
    student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
    
    # 4. Delete Grades and Student Profile if they exist
    if student:
        db.query(models.Grade).filter(models.Grade.student_id == student.id).delete()
        db.delete(student)
    
    # 5. Delete User
    db.delete(user)
    db.commit()
    
    return {"message": "Child deleted successfully"}

@app.put("/users/{user_id}/password")
def update_password(user_id: int, user_update: UserPasswordUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = get_password_hash(user_update.password)
    db_user.password_hash = hashed_password
    db.commit()
    return {"message": "Password updated successfully"}

@app.post("/subjects/", response_model=Subject)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Scope to current user (if parent) or parent (if student)
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
        
    db_subject = models.Subject(name=subject.name, weighting=subject.weighting, owner_id=owner_id)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@app.get("/subjects/", response_model=List[Subject])
def read_subjects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Filter by owner_id
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
        
    subjects = db.query(models.Subject).filter(models.Subject.owner_id == owner_id).offset(skip).limit(limit).all()
    return subjects

@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    # Check ownership
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
    
    if subject.owner_id != owner_id and current_user.role != 'admin': # Admin override
         raise HTTPException(status_code=403, detail="Not authorized to delete this subject")

    # Manually delete grades associated with this subject (safeguard for SQLite/no-cascade)
    db.query(models.Grade).filter(models.Grade.subject_id == subject_id).delete()
    
    db.delete(subject)
    db.commit()
    return {"message": "Subject and associated grades deleted"}

@app.post("/grades/", response_model=Grade)
def create_grade(grade: GradeCreate, student_id: int = 1, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Check if student exists
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    
    # Authorized?
    # 1. Student adding their own grade
    # 2. Parent adding grade for their child
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # If current_user is a student, they must be the student_id
    if current_user.role == "student":
        if current_user.student_profile and current_user.student_profile.id != student_id:
             raise HTTPException(status_code=403, detail="Cannot add grades for other students")
    
    # If current_user is a parent, the student must be their child
    if current_user.role == "parent":
         child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
         if not child_user or child_user.parent_id != current_user.id:
              raise HTTPException(status_code=403, detail="Not authorized to add grades for this student")

    # Validate that the subject exists and belongs to the correct owner
    subject = db.query(models.Subject).filter(models.Subject.id == grade.subject_id).first()
    if not subject:
         raise HTTPException(status_code=404, detail="Subject not found")
         
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
    if subject.owner_id != owner_id and current_user.role != 'admin':
         raise HTTPException(status_code=403, detail="Not authorized to use this subject")
    
    db_grade = models.Grade(**grade.model_dump(), student_id=student_id) if hasattr(grade, "model_dump") else models.Grade(**grade.dict(), student_id=student_id)
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

@app.get("/grades/", response_model=List[Grade])
def read_grades(student_id: int = 1, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Auth Check
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        # If no student found, return empty or 404. 
        # But we should check auth first if possible.
        pass

    # Simplified Auth Check similar to create_grade
    if current_user.role == "student":
        if current_user.student_profile and current_user.student_profile.id != student_id:
             raise HTTPException(status_code=403, detail="Cannot view grades for other students")
    
    if current_user.role == "parent":
         child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
         if not child_user or child_user.parent_id != current_user.id:
              raise HTTPException(status_code=403, detail="Not authorized to view grades for this student")

    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    return grades

@app.delete("/grades/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    student = db.query(models.Student).filter(models.Student.id == grade.student_id).first()
    if student:
        if current_user.role == "student":
            if current_user.student_profile and current_user.student_profile.id != student.id:
                raise HTTPException(status_code=403, detail="Cannot delete grades for other students")
        if current_user.role == "parent":
            child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
            if not child_user or child_user.parent_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to delete grades for this student")
                
    db.delete(grade)
    db.commit()
    return {"message": "Grade deleted"}

@app.get("/average/")
def calculate_average(student_id: int = 1, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
     # Auth Check (Same as read_grades)
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    
    if current_user.role == "student":
        if current_user.student_profile and current_user.student_profile.id != student_id:
             raise HTTPException(status_code=403, detail="Cannot view grades for other students")
    
    if current_user.role == "parent":
         child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
         if not child_user or child_user.parent_id != current_user.id:
              raise HTTPException(status_code=403, detail="Not authorized to view grades for this student")

    # Calculate Gymi Score based on specific rules
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    
    # Helpers
    def get_grades(subj_name, g_types=None):
        # Support single string or list of strings
        if isinstance(g_types, str):
            g_types = [g_types]
        return [g.value for g in grades if g.subject and g.subject.name == subj_name and (not g_types or g.type in g_types)]
    
    def avg(values):
        return sum(values) / len(values) if values else None

    # Vornote / Schulprüfung: 50% Deutsch, 50% Math
    # Support both old "Vornote" and new "Schulprüfung" tags
    math_vornote_grades = get_grades("Mathematik", ["Vornote", "Schulprüfung"])
    deutsch_vornote_grades = get_grades("Deutsch", ["Vornote", "Schulprüfung"])
    
    math_vornote = avg(math_vornote_grades)
    deutsch_vornote = avg(deutsch_vornote_grades)
    
    overall_vornote = None
    if math_vornote is not None and deutsch_vornote is not None:
        overall_vornote = (math_vornote + deutsch_vornote) / 2
    elif math_vornote is not None:
        overall_vornote = math_vornote
    elif deutsch_vornote is not None:
        overall_vornote = deutsch_vornote
        
    # Prüfungsnote / Gymiprüfung: 50% Math Exam, 50% Deutsch Exam
    # Math Exam: Type "Prüfung" or "Gymiprüfung"
    # Deutsch Exam: "Aufsatz", "Aufsatz (Gymiprüfung)", etc.
    
    math_exam_grades = get_grades("Mathematik", ["Prüfung", "Gymiprüfung"])
    math_exam = avg(math_exam_grades)
    
    deutsch_aufsatz = avg(get_grades("Deutsch", ["Aufsatz", "Aufsatz (Prüfung)", "Aufsatz (Gymiprüfung)"]))
    deutsch_sprach = avg(get_grades("Deutsch", ["Sprachbetrachtung", "Sprachbetrachtung (Prüfung)", "Sprachbetrachtung (Gymiprüfung)"]))
    
    deutsch_exam = None
    if deutsch_aufsatz is not None and deutsch_sprach is not None:
        deutsch_exam = (deutsch_aufsatz + deutsch_sprach) / 2
    elif deutsch_aufsatz is not None: 
         deutsch_exam = deutsch_aufsatz # Fallback if incomplete
    elif deutsch_sprach is not None:
         deutsch_exam = deutsch_sprach # Fallback
         
    # Overall Exam
    overall_exam = None
    if math_exam is not None and deutsch_exam is not None:
        overall_exam = (math_exam + deutsch_exam) / 2
    elif math_exam is not None:
        overall_exam = math_exam
    elif deutsch_exam is not None:
        overall_exam = deutsch_exam

    # Gesamtnote
    gesamtnote = 0.0
    if overall_vornote is not None and overall_exam is not None:
        gesamtnote = (overall_vornote + overall_exam) / 2
    elif overall_vornote is not None:
        gesamtnote = overall_vornote
    elif overall_exam is not None:
        gesamtnote = overall_exam
        
    passed = gesamtnote >= 4.75
    
    return {
        "average": round(gesamtnote, 2),
        "details": {
            "vornote": {
                "value": round(overall_vornote, 2) if overall_vornote else None,
                "math": round(math_vornote, 2) if math_vornote else None,
                "deutsch": round(deutsch_vornote, 2) if deutsch_vornote else None
            },
            "exam": {
                "value": round(overall_exam, 2) if overall_exam else None,
                "math": round(math_exam, 2) if math_exam else None,
                "deutsch": {
                    "value": round(deutsch_exam, 2) if deutsch_exam else None,
                    "aufsatz": round(deutsch_aufsatz, 2) if deutsch_aufsatz else None,
                    "sprachbetrachtung": round(deutsch_sprach, 2) if deutsch_sprach else None
                }
            }
        },
        "passed": passed
    }

@app.post("/analyze-exam")
def analyze_exam(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Mock Response
    return {
        "grade": 5.0,
        "subject": "Deutsch",
        "feedback": "Gute Arbeit bei der Textanalyse, aber achte mehr auf die Kommasetzung!"
    }

# --- Topic Endpoints ---

class TopicBase(BaseModel):
    name: str = Field(..., pattern=SAFE_TEXT_REGEX, min_length=2, max_length=100)
    is_completed: bool = False

class TopicCreate(TopicBase):
    subject_id: int

class Topic(TopicBase):
    id: int
    subject_id: int
    class Config:
        from_attributes = True

@app.post("/topics/", response_model=Topic)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    subject = db.query(models.Subject).filter(models.Subject.id == topic.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
    if subject.owner_id != owner_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to add topics to this subject")

    db_topic = models.Topic(name=topic.name, is_completed=topic.is_completed, subject_id=topic.subject_id)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@app.put("/topics/{topic_id}/toggle", response_model=Topic)
def toggle_topic(topic_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    subject = db.query(models.Subject).filter(models.Subject.id == topic.subject_id).first()
    if subject:
        owner_id = current_user.id
        if current_user.role == "student" and current_user.parent_id:
            owner_id = current_user.parent_id
        if subject.owner_id != owner_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized to toggle this topic")
            
    topic.is_completed = not topic.is_completed
    db.commit()
    db.refresh(topic)
    return topic

@app.get("/subjects/{subject_id}/topics", response_model=List[Topic])
def read_topics(subject_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
    if subject.owner_id != owner_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
        
    topics = db.query(models.Topic).filter(models.Topic.subject_id == subject_id).all()
    return topics

# --- Prediction Endpoint ---

class PredictionRequest(BaseModel):
    target_average: float
    next_exam_weight: float = 1.0

@app.post("/prediction")
def predict_grade(request: PredictionRequest, student_id: int = 1, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Auth Check (Same as read_grades)
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    
    if current_user.role == "student":
        if current_user.student_profile and current_user.student_profile.id != student_id:
             raise HTTPException(status_code=403, detail="Cannot view grades for other students")
    
    if current_user.role == "parent":
         child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
         if not child_user or child_user.parent_id != current_user.id:
              raise HTTPException(status_code=403, detail="Not authorized to view grades for this student")

    # 1. Calculate current state
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    
    total_score = 0
    total_weight = 0
    
    for grade in grades:
        subject = db.query(models.Subject).filter(models.Subject.id == grade.subject_id).first()
        if subject:
            total_score += grade.value * subject.weighting
            total_weight += subject.weighting
    
    if total_weight == 0:
        return {"required_grade": request.target_average, "message": "Noch keine Noten vorhanden."}

    # 2. Formula: x = ( T * (W + w) - Av*W ) / w
    # Simplified: x = ( T * (W + w) - TotalScore ) / w
    
    target = request.target_average
    w = request.next_exam_weight
    W = total_weight
    CurrentScore = total_score
    
    required_value = (target * (W + w) - CurrentScore) / w
    required_value = round(required_value, 2)
    
    return {
        "required_grade": required_value,
        "current_weight": total_weight,
        "next_weight": w
    }

# --- AI Chat Endpoint ---

class ChatRequest(BaseModel):
    message: str
    student_id: Optional[int] = None

def get_student_context(student_id: int, db: Session):
    """
    Fetches relevant student data to build a context string for the AI.
    """
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return "Student not found."

    # Fetch subjects and grades
    subjects = db.query(models.Subject).all()
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    
    # Organize grades by subject
    subject_context = []
    for subject in subjects:
        subj_grades = [g.value for g in grades if g.subject_id == subject.id]
        avg = sum(subj_grades) / len(subj_grades) if subj_grades else 0.0
        avg_str = f"{avg:.2f}" if subj_grades else "No grades yet"
        subject_context.append(f"- {subject.name}: Average {avg_str} (Grades: {subj_grades})")
    
    # Fetch Topics
    topics = db.query(models.Topic).join(models.Subject).all() # This fetches all topics, filter by student?
    # Topics are global definitions, but completion is specific? 
    # Wait, models.Topic has 'is_completed' column.
    # Checking models.py: Topic.is_completed is an Integer column on the Topic table itself.
    # This implies Topics are NOT per student currently in this simple schema, but shared/global state 
    # OR the schema meant for single user demo. 
    # Given the 'reset' endpoint resets all topics, it seems topics are shared or single-instance.
    # We will just list them as is.
    
    topic_context = []
    for t in topics:
        status = "[x]" if t.is_completed else "[ ]"
        topic_context.append(f"{status} {t.name} ({t.subject.name if t.subject else 'Unknown'})")
    
    context_str = f"""
    Student Name: {student.name}
    Target School: {student.target_school}
    
    Academic Performance:
    {chr(10).join(subject_context)}
    
    Learning Topics Status:
    {chr(10).join(topic_context)}
    """
    return context_str

@app.post("/chat")
def chat_bot(request: ChatRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Determine Student ID
    target_student_id = None
    
    if request.student_id:
        # Client requested specific student check auth
        if current_user.role == "student":
            if current_user.student_profile and current_user.student_profile.id == request.student_id:
                target_student_id = request.student_id
        elif current_user.role == "parent":
             # Check if child belongs to parent
             # Need to find the user associated with this student_id
             student = db.query(models.Student).filter(models.Student.id == request.student_id).first()
             if student:
                 child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
                 if child_user and child_user.parent_id == current_user.id:
                     target_student_id = request.student_id
    else:
        # Fallback / Default
        if current_user.role == "student" and current_user.student_profile:
            target_student_id = current_user.student_profile.id
            
    if not target_student_id:
        # If we can't context, just chat generically or error?
        # Let's try to proceed with generic chat but warn or just generic.
        pass

    # 2. Build Context
    context = ""
    
    if current_user.role == "parent":
        # Parent Context: Fetch ALL children
        children_users = db.query(models.User).filter(models.User.parent_id == current_user.id).all()
        
        if not children_users:
            context = "No children linked to this parent account."
        else:
            context_parts = []
            for child_user in children_users:
                # Get student profile for this child
                student_profile = db.query(models.Student).filter(models.Student.user_id == child_user.id).first()
                if student_profile:
                    child_context = get_student_context(student_profile.id, db)
                    # Add a header for the child
                    context_parts.append(f"--- Child: {student_profile.name} (ID: {student_profile.id}) ---\n{child_context}")
            
            context = "Here is the data for your children:\n\n" + "\n\n".join(context_parts)
            
            if target_student_id:
                # If a specific child was selected, mention it
                selected_student = db.query(models.Student).filter(models.Student.id == target_student_id).first()
                if selected_student:
                    context = f"CURRENTLY VIEWING: {selected_student.name}\n\n" + context
    
    elif target_student_id:
        # Student Context (Single)
        context = get_student_context(target_student_id, db)
    
    # 3. Call OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
         return {"response": "Brain not connected (API Key missing)."}

    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = ""
    
    grading_system_context = """
    IMPORTANT - GRADING SYSTEM (Swiss Standard):
    - Scale: 1.0 to 6.0
    - 6.0 = Excellent / Best possible grade
    - 5.0 = Good
    - 4.0 = Sufficient (Pass)
    - Below 4.0 = Insufficient (Fail)
    - 1.0 = Worst possible grade
    PLEASE INTERPRET ALL GRADES ACCORDING TO THIS SYSTEM. A 5.5 is amazing, a 2.5 is very bad.
    """

    formatting_instruction = "\nIMPORTANT: Format your response using Markdown. Use **bold** for emphasis, lists for readability, and headers (###) for sections."

    gym_exam_context = """
    GOAL: Prepare the student for the 'Gymnasiumsaufnahmeprüfung' (Swiss Gymnasium Entrance Exam).
    - Focus on core subjects: Mathematics and German (and potentially French/English).
    - When asked for exercises, suggest tasks typical for Swiss Gymi exams (e.g., text analysis in German, geometry/word problems in Math).
    - Motivate the student for this specific high-stakes goal.
    """

    if current_user.role == "parent":
        system_prompt = f"""You are a helpful education advisor for a parent.
        Your goal is to help the parent understand their child's progress, interpret grades, and suggest supportive actions to help the child pass the Gymnasium Entrance Exam.
        
        {grading_system_context}
        {gym_exam_context}
        {formatting_instruction}
        
        Child's Current Context:
        {context}
        
        Instructions:
        - Address the user as the parent.
        - Be professional but empathetic.
        - Analyze the grades objectively (e.g., "The math grades have improved...").
        - Suggest specific topics the parent can help the child review based on the topic status.
        - Do not address the child directly; address the parent about the child.
        """
    else:
        # Default to student "Lern-Coach"
        system_prompt = f"""You are a helpful, encouraging learning coach for a student.
        Your goal is to help them learn, reflect on their grades, and prepare for the Gymnasium Entrance Exam.
        
        {grading_system_context}
        {gym_exam_context}
        {formatting_instruction}
        
        Current Student Context:
        {context}
        
        Instructions:
        - Be friendly and age-appropriate (for school kids).
        - Use the grades context to give specific advice (e.g. "Math looks great, but let's practice German").
        - Do NOT give direct answers to homework questions, but guide them.
        """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return {"response": "Entschuldigung, ich bin gerade etwas verwirrt. Versuche es später nochmal."}


@app.post("/reset")
def reset_demo(student_id: int = 1, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Validate ownership of the student
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    if current_user.role == "student":
        if current_user.student_profile and current_user.student_profile.id != student_id:
             raise HTTPException(status_code=403, detail="Cannot reset data for other students")
    
    if current_user.role == "parent":
         child_user = db.query(models.User).filter(models.User.id == student.user_id).first()
         if not child_user or child_user.parent_id != current_user.id:
              raise HTTPException(status_code=403, detail="Not authorized to reset data for this student")
              
    owner_id = current_user.id
    if current_user.role == "student" and current_user.parent_id:
        owner_id = current_user.parent_id
        
    # Delete all grades for student
    db.query(models.Grade).filter(models.Grade.student_id == student_id).delete()
    
    # Reset all topics to not completed ONLY for subjects owned by this user/parent
    subjects = db.query(models.Subject).filter(models.Subject.owner_id == owner_id).all()
    subject_ids = [s.id for s in subjects]
    if subject_ids:
        topics = db.query(models.Topic).filter(models.Topic.subject_id.in_(subject_ids)).all()
        for t in topics:
            t.is_completed = 0
    
    db.commit()
    return {"message": "Demo reset successful"}

