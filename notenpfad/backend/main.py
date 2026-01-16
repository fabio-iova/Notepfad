from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from passlib.context import CryptContext
import models, database

models.Base.metadata.create_all(bind=database.engine)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Notenpfad API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
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

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- Pydantic Schemas ---
class GradeBase(BaseModel):
    value: float
    subject_id: int
    type: str = "Exam"
    date: date

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: int
    student_id: int
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserStudentCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserPasswordUpdate(BaseModel):
    password: str

class ChildCreate(UserBase):
    password: str
    name: str
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
        orm_mode = True

class SubjectBase(BaseModel):
    name: str
    weighting: float = 1.0

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: int
    grades: List[Grade] = []
    class Config:
        orm_mode = True

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
    try:
        # 1. Create Admin (Parent)
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin:
            print("Creating default admin user")
            hashed_password = get_password_hash("1234")
            admin = models.User(username="admin", password_hash=hashed_password, role="parent")
            db.add(admin)
            db.commit()
            db.refresh(admin)
        
        # 2. Create Sole (Student) linked to Admin
        sole = db.query(models.User).filter(models.User.username == "sole").first()
        if not sole:
            print("Creating default student user: sole")
            hashed_sole_pw = get_password_hash("sun26")
            sole = models.User(username="sole", password_hash=hashed_sole_pw, role="student", parent_id=admin.id)
            db.add(sole)
            db.commit()
            db.refresh(sole)

        # 3. Create Student Profile for Sole (if not exists)
        # Check if Linked Student Profile exists
        student_profile = db.query(models.Student).filter(models.Student.user_id == sole.id).first()
        if not student_profile:
             print("Creating student profile for sole")
             student_profile = models.Student(name="Sole Iovanna", target_school="Gymnasium", user_id=sole.id)
             db.add(student_profile)
             db.commit()

    finally:
        db.close()

@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
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
def create_student(user: UserStudentCreate, db: Session = Depends(get_db)):
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

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Return role in login response
    # Find linked student_id if applicable
    student_id = None
    if db_user.student_profile:
        student_id = db_user.student_profile.id

    return {
        "message": "Login successful", 
        "user_id": db_user.id, 
        "username": db_user.username,
        "role": db_user.role,
        "student_id": student_id
    }

@app.post("/users/children", response_model=UserOut)
def create_child(child: ChildCreate, db: Session = Depends(get_db)):
    # Check parent exists
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
def get_children(user_id: int, db: Session = Depends(get_db)):
    children = db.query(models.User).filter(models.User.parent_id == user_id).all()
    return children

@app.delete("/users/children/{child_id}")
def delete_child(child_id: int, db: Session = Depends(get_db)):
    # 1. Find User
    user = db.query(models.User).filter(models.User.id == child_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
def update_password(user_id: int, user_update: UserPasswordUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = get_password_hash(user_update.password)
    db_user.password_hash = hashed_password
    db.commit()
    return {"message": "Password updated successfully"}

@app.post("/subjects/", response_model=Subject)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    db_subject = models.Subject(name=subject.name, weighting=subject.weighting)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@app.get("/subjects/", response_model=List[Subject])
def read_subjects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    subjects = db.query(models.Subject).offset(skip).limit(limit).all()
    return subjects

@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Manually delete grades associated with this subject (safeguard for SQLite/no-cascade)
    db.query(models.Grade).filter(models.Grade.subject_id == subject_id).delete()
    
    db.delete(subject)
    db.commit()
    return {"message": "Subject and associated grades deleted"}

@app.post("/grades/", response_model=Grade)
def create_grade(grade: GradeCreate, student_id: int = 1, db: Session = Depends(get_db)):
    # Check if student exists
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db_grade = models.Grade(**grade.dict(), student_id=student_id)
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

@app.get("/grades/", response_model=List[Grade])
def read_grades(student_id: int = 1, db: Session = Depends(get_db)):
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    return grades

@app.delete("/grades/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    db.delete(grade)
    db.commit()
    return {"message": "Grade deleted"}

@app.get("/average/")
def calculate_average(student_id: int = 1, db: Session = Depends(get_db)):
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
def analyze_exam():
    # Mock Response
    return {
        "grade": 5.0,
        "subject": "Deutsch",
        "feedback": "Gute Arbeit bei der Textanalyse, aber achte mehr auf die Kommasetzung!"
    }

# --- Topic Endpoints ---

class TopicBase(BaseModel):
    name: str
    is_completed: bool = False

class TopicCreate(TopicBase):
    subject_id: int

class Topic(TopicBase):
    id: int
    subject_id: int
    class Config:
        from_attributes = True

@app.post("/topics/", response_model=Topic)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    db_topic = models.Topic(name=topic.name, is_completed=topic.is_completed, subject_id=topic.subject_id)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@app.put("/topics/{topic_id}/toggle", response_model=Topic)
def toggle_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    topic.is_completed = not topic.is_completed
    db.commit()
    db.refresh(topic)
    return topic

@app.get("/subjects/{subject_id}/topics", response_model=List[Topic])
def read_topics(subject_id: int, db: Session = Depends(get_db)):
    topics = db.query(models.Topic).filter(models.Topic.subject_id == subject_id).all()
    return topics

# --- Prediction Endpoint ---

class PredictionRequest(BaseModel):
    target_average: float
    next_exam_weight: float = 1.0

@app.post("/prediction")
def predict_grade(request: PredictionRequest, student_id: int = 1, db: Session = Depends(get_db)):
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

@app.post("/chat")
def chat_bot(request: ChatRequest):
    msg = request.message.lower()
    
    # Simple keyword-based mocked AI for now
    if "hallo" in msg:
        return {"response": "Hi! Bereit zum Lernen? 📚"}
    elif "mathe" in msg:
        return {"response": "Mathe kann knifflig sein. Probiere es mit Übungsaufgaben zu Brüchen!"}
    elif "deutsch" in msg:
        return {"response": "Für Deutsch empfehle ich: Lesen, Lesen, Lesen! 📖"}
    elif "prüfung" in msg:
        return {"response": "Keine Panik vor der Prüfung. Atme tief durch und geh Schritt für Schritt vor."}
    else:
        return {"response": "Das ist interessant. Erzähl mir mehr oder frag mich nach einem bestimmten Fach."}

@app.post("/reset")
def reset_demo(student_id: int = 1, db: Session = Depends(get_db)):
    # Delete all grades for student
    db.query(models.Grade).filter(models.Grade.student_id == student_id).delete()
    
    # Reset all topics to not completed
    topics = db.query(models.Topic).all()
    for t in topics:
        t.is_completed = 0
    
    db.commit()
    return {"message": "Demo reset successful"}

