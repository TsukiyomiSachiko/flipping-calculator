"""
Migration 008: Add mutation_type to flip_transactions

Allows tracking configuration changes (price updates, target adjustments) 
in the transaction log.
"""
import os
import sys

# Add the project root to sys.path to allow importing from app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.database import get_db, engine

def migrate():
    is_sqlite = 'sqlite' in str(engine.url)
    print(f"Migrating {'SQLite' if is_sqlite else 'PostgreSQL'} database...")

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if column exists
        if is_sqlite:
            cursor.execute("PRAGMA table_info(flip_transactions)")
            columns = [col[1] for col in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'flip_transactions'
            """)
            columns = [col[0] for col in cursor.fetchall()]
        
        if 'mutation_type' not in columns:
            print("Adding mutation_type column...")
            if is_sqlite:
                cursor.execute("ALTER TABLE flip_transactions ADD COLUMN mutation_type TEXT")
            else:
                cursor.execute("ALTER TABLE flip_transactions ADD COLUMN mutation_type TEXT")
            
            # Make quantity and price nullable for mutation logs
            # SQLite doesn't support ALTER COLUMN, so we just rely on it being flexible
            # Postgres needs explicit ALTER COLUMN
            if not is_sqlite:
                cursor.execute("ALTER TABLE flip_transactions ALTER COLUMN quantity DROP NOT NULL")
                cursor.execute("ALTER TABLE flip_transactions ALTER COLUMN price DROP NOT NULL")
            
            # Backfill existing transactions as 'trade' mutation type
            cursor.execute("UPDATE flip_transactions SET mutation_type = 'trade' WHERE mutation_type IS NULL")
            print("Migration successful!")
        else:
            print("mutation_type column already exists.")

if __name__ == "__main__":
    migrate()
