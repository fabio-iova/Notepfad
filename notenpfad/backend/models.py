from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    target_school = Column(String)
    user_id = Column(Integer, ForeignKey("users.id")) # Link to login account

    grades = relationship("Grade", back_populates="student")
    user = relationship("User", back_populates="student_profile")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    weighting = Column(Float, default=1.0)

    grades = relationship("Grade", back_populates="subject")
    topics = relationship("Topic", back_populates="subject")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    is_completed = Column(Integer, default=0) # 0 = false, 1 = true (SQLite has no bool)
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    subject = relationship("Subject", back_populates="topics")

class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float)
    date = Column(Date)
    type = Column(String) # e.g., "Exam", "Oral"
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="parent") # parent, student
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    children = relationship("User", back_populates="parent", remote_side=[id])
    parent = relationship("User", back_populates="children", remote_side=[parent_id])
    student_profile = relationship("Student", back_populates="user", uselist=False)
