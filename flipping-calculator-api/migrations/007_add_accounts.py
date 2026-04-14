"""
Migration: Add accounts table and link flips/settings to accounts.
"""

import logging
from app.utils.database import get_db, engine

logger = logging.getLogger(__name__)

def migrate():
    is_sqlite = 'sqlite' in str(engine.url)
    pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        logger.info("Creating accounts table...")
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS accounts (
                id {pk_type},
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if QueenieTsuki exists, if not create it
        cursor.execute("SELECT id FROM accounts WHERE name = 'QueenieTsuki'")
        row = cursor.fetchone()
        if not row:
            logger.info("Creating 'QueenieTsuki' account...")
            cursor.execute("INSERT INTO accounts (name) VALUES ('QueenieTsuki')")
            cursor.execute("SELECT id FROM accounts WHERE name = 'QueenieTsuki'")
            account_id = cursor.fetchone()['id']
        else:
            account_id = row['id']
            
        logger.info(f"QueenieTsuki account ID: {account_id}")
        
        # Add account_id to user_flips
        logger.info("Adding account_id to user_flips...")
        try:
            cursor.execute("ALTER TABLE user_flips ADD COLUMN account_id INTEGER")
        except Exception as e:
            logger.info(f"Column account_id might already exist in user_flips: {e}")
            
        # Update existing flips to QueenieTsuki
        cursor.execute("UPDATE user_flips SET account_id = ? WHERE account_id IS NULL", (account_id,))
        
        # Add foreign key constraint (SQLite doesn't support adding FKs to existing tables easily, 
        # but we can do it for Postgres or just leave it for SQLite)
        if not is_sqlite:
            try:
                cursor.execute("ALTER TABLE user_flips ADD CONSTRAINT fk_user_flips_account FOREIGN KEY (account_id) REFERENCES accounts(id)")
            except Exception as e:
                logger.info(f"Constraint might already exist: {e}")
                
        # Update user_settings
        logger.info("Migrating user_settings...")
        
        # Create new user_settings table if needed, or modify existing
        if is_sqlite:
            # For SQLite we might need to recreate the table to remove the CHECK constraint
            cursor.execute("ALTER TABLE user_settings RENAME TO user_settings_old")
            cursor.execute(f'''
                CREATE TABLE user_settings (
                    id {pk_type},
                    account_id INTEGER NOT NULL UNIQUE,
                    available_cash BIGINT DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            ''')
            # Copy data for account 1 to QueenieTsuki
            cursor.execute('''
                INSERT INTO user_settings (account_id, available_cash, last_updated)
                SELECT ?, available_cash, last_updated FROM user_settings_old WHERE id = 1
            ''', (account_id,))
            cursor.execute("DROP TABLE user_settings_old")
        else:
            # Postgres: remove check constraint and add account_id
            try:
                # Find the name of the check constraint
                cursor.execute("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE conrelid = 'user_settings'::regclass AND contype = 'c'
                """)
                constraints = cursor.fetchall()
                for c in constraints:
                    cursor.execute(f"ALTER TABLE user_settings DROP CONSTRAINT {c['conname']}")
                
                cursor.execute("ALTER TABLE user_settings ADD COLUMN account_id INTEGER")
                cursor.execute("UPDATE user_settings SET account_id = ? WHERE account_id IS NULL", (account_id,))
                cursor.execute("ALTER TABLE user_settings ALTER COLUMN account_id SET NOT NULL")
                cursor.execute("ALTER TABLE user_settings ADD CONSTRAINT unique_account_settings UNIQUE (account_id)")
                cursor.execute("ALTER TABLE user_settings ADD CONSTRAINT fk_user_settings_account FOREIGN KEY (account_id) REFERENCES accounts(id)")
            except Exception as e:
                logger.info(f"Error updating user_settings for Postgres: {e}")

        conn.commit()
        logger.info("Migration completed successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate()
