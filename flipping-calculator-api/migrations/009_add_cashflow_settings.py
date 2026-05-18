"""
Migration 009: Add profit_take_pct and loss_refill_pct to user_settings

Allows users to manage cashflow settings for profits and losses.
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

        # Check if columns exist
        if is_sqlite:
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = [col[1] for col in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user_settings'
            """)
            columns = [col[0] for col in cursor.fetchall()]

        if 'profit_take_pct' not in columns:
            print("Adding profit_take_pct column...")
            cursor.execute("ALTER TABLE user_settings ADD COLUMN profit_take_pct FLOAT DEFAULT 0")
        else:
            print("profit_take_pct column already exists.")

        if 'loss_refill_pct' not in columns:
            print("Adding loss_refill_pct column...")
            cursor.execute("ALTER TABLE user_settings ADD COLUMN loss_refill_pct FLOAT DEFAULT 0")
        else:
            print("loss_refill_pct column already exists.")

        conn.commit()
        print("Migration successful!")

if __name__ == "__main__":
    migrate()
