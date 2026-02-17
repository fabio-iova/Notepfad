from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# Debug Logging
print("--- DATABASE CONFIGURATION ---")
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    print("WARNING: Using SQLite database! This is ephemeral on Railway.")
    print(f"Database Path: {SQLALCHEMY_DATABASE_URL}")
else:
    print("INFO: Using remote database connection.")
    # Mask password for logs
    safe_url = SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else "..."
    print(f"Target: ...@{safe_url}")

# SQLAlchemy requires postgresql:// but Railway provides postgres://
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
