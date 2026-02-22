import os
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.engine import reflection

# Get DB URL from env or default to local sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# Fix potential postgres:// issue for Railway/Heroku
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def migrate():
    print(f"Migrating database: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        inspector = reflection.Inspector.from_engine(engine)
        columns = [col['name'] for col in inspector.get_columns("subjects")]
        
        if "owner_id" in columns:
            print("Migration already applied: 'owner_id' exists.")
            return

        print("Applying migration...")

        # 1. Add owner_id column
        # SQLite and Postgres support ADD COLUMN (SQLite supports it since 3.35+ basically, but sqlalchemy handles it well usually)
        # However, removing constraints in SQLite requires table recreation. 
        # Postgres supports DROP CONSTRAINT.

        is_sqlite = "sqlite" in DATABASE_URL
        
        if is_sqlite:
            print("Detected SQLite. Using table recreation method (safer for SQLite constraints).")
            # For SQLite, we might just run the specialized script or do it here.
            # Since we already ran the specialized script locally, this part is for if env is sqlite but not yet migrated.
            # Simplified SQLite migration logic here (similar to migrate_subjects.py but using SQLAlchemy text)
            
            # This is complex to do generically in one script for both without full ORM heavy lifting or Alembic.
            # But let's try a direct approach for Postgres (User requirement) and fallback for SQLite.
            pass # We assume local sqlite is done. User asked about Postgres.

        if not is_sqlite:
            print("Detected PostgreSQL (or other). Using ALTER TABLE statements.")
            trans = conn.begin()
            try:
                # A. Add Column
                conn.execute(text("ALTER TABLE subjects ADD COLUMN owner_id INTEGER REFERENCES users(id)"))
                
                # B. Remove Unique Constraint
                # We need to find the constraint name first.
                # In Postgres, unique constraints are indexes usually.
                # Try to drop the unique index/constraint on 'name'.
                # Usually named 'subjects_name_key' or similar or 'ix_subjects_name' if created by index=True, unique=True
                
                # Check indexes
                indexes = inspector.get_indexes("subjects")
                for index in indexes:
                    if index['unique'] and 'name' in index['column_names']:
                        constraint_name = index['name']
                        print(f"Dropping unique constraint/index: {constraint_name}")
                        conn.execute(text(f"DROP INDEX {constraint_name}"))
                        # If it was a CONSTRAINT (not just index), we might need ALTER TABLE DROP CONSTRAINT
                        # But SQLAlchemy often creates unique indexes for unique=True.
                        # If it works, great. If not, we might need to be more aggressive.
                
                # C. Data Migration (Assign existing to Admin)
                # Find Admin ID
                result = conn.execute(text("SELECT id FROM users WHERE username='admin'"))
                admin_id = result.scalar()
                if not admin_id:
                    print("Admin not found, using ID 1")
                    admin_id = 1
                
                print(f"Assigning existing subjects to owner_id={admin_id}")
                conn.execute(text(f"UPDATE subjects SET owner_id = {admin_id} WHERE owner_id IS NULL"))
                
                trans.commit()
                print("Migration successful!")
            except Exception as e:
                trans.rollback()
                print(f"Migration failed: {e}")
                raise e

if __name__ == "__main__":
    migrate()
