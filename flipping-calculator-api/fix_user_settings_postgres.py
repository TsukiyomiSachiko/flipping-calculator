"""
Fix for user_settings table in PostgreSQL to ensure auto-incrementing ID.
"""

import logging
from app.utils.database import get_db, engine

logger = logging.getLogger(__name__)

def fix():
    is_sqlite = 'sqlite' in str(engine.url)
    if is_sqlite:
        logger.info("Skipping PostgreSQL fix for SQLite database.")
        return

    with get_db() as conn:
        cursor = conn.cursor()
        
        logger.info("Applying PostgreSQL fix for user_settings table...")
        
        try:
            # Create sequence if it doesn't exist
            cursor.execute("CREATE SEQUENCE IF NOT EXISTS user_settings_id_seq")
            
            # Set default value for id column
            cursor.execute("ALTER TABLE user_settings ALTER COLUMN id SET DEFAULT nextval('user_settings_id_seq')")
            
            # Synchronize sequence with current max ID
            cursor.execute("SELECT setval('user_settings_id_seq', (SELECT COALESCE(MAX(id), 0) FROM user_settings) + 1, false)")
            
            conn.commit()
            logger.info("✅ PostgreSQL fix applied successfully!")
        except Exception as e:
            logger.error(f"Error applying PostgreSQL fix: {e}")
            conn.rollback()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix()
