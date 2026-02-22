import sqlite3
import shutil
import os

DB_FILE = "database.db"
BACKUP_FILE = "database.db.bak"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found.")
        return

    # 1. Backup
    shutil.copy(DB_FILE, BACKUP_FILE)
    print(f"Backed up database to {BACKUP_FILE}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if column already exists to avoid double migration
        cursor.execute("PRAGMA table_info(subjects)")
        columns = [info[1] for info in cursor.fetchall()]
        if "owner_id" in columns:
            print("Migration already applied: 'owner_id' exists in 'subjects'.")
            return

        print("Starting migration...")

        # 2. Rename old table
        cursor.execute("ALTER TABLE subjects RENAME TO subjects_old")

        # 3. Create new table (Note: owner_id added, UNIQUE constraint on name REMOVED)
        cursor.execute("""
            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                weighting FLOAT,
                owner_id INTEGER REFERENCES users(id)
            )
        """)
        
        # 4. Copy data
        # We assign all existing subjects to the admin user (ID 1) or leave owner_id NULL if generic?
        # Let's assign to ID 1 (Admin) to be safe, assuming Admin is ID 1.
        # Actually, let's check who the admin is.
        cursor.execute("SELECT id FROM users WHERE username='admin'")
        admin_row = cursor.fetchone()
        admin_id = admin_row[0] if admin_row else 1 

        print(f"Assigning existing subjects to Admin (ID {admin_id})...")

        cursor.execute(f"""
            INSERT INTO subjects (id, name, weighting, owner_id)
            SELECT id, name, weighting, {admin_id} FROM subjects_old
        """)

        # 5. Drop old table
        cursor.execute("DROP TABLE subjects_old")
        
        # 6. Create Indexes
        cursor.execute("CREATE INDEX ix_subjects_id ON subjects (id)")
        cursor.execute("CREATE INDEX ix_subjects_name ON subjects (name)")
        cursor.execute("CREATE INDEX ix_subjects_owner_id ON subjects (owner_id)")

        conn.commit()
        print("Migration successful!")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        print("Rolled back changes. Restoring backup...")
        shutil.copy(BACKUP_FILE, DB_FILE)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
