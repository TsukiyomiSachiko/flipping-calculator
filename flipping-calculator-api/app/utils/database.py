"""
PostgreSQL Database Configuration

Replaces SQLite with PostgreSQL for better concurrency and performance.
Includes compatibility layer for existing cursor-based code.
"""

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

logger = logging.getLogger(__name__)

# Database URL from environment or default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://flipping_user:flipping_dev_password@localhost/osrs_flipping'
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Max 10 connections in pool
    max_overflow=20,       # Allow 20 more if needed
    pool_pre_ping=True,    # Check connection before using
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False             # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class RowProxy:
    """Makes SQLAlchemy result rows behave like SQLite Row objects"""
    def __init__(self, keys, values):
        self._keys = keys
        self._values = values
        self._dict = dict(zip(keys, values))
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._dict[key]
    
    def keys(self):
        return self._keys
    
    def __iter__(self):
        return iter(self._values)


class CursorWrapper:
    """Makes SQLAlchemy session behave like SQLite cursor for compatibility"""
    def __init__(self, session):
        self.session = session
        self._result = None
        self.rowcount = 0
        self.lastrowid = None
    
    def execute(self, query, params=None):
        # Convert ? placeholders to :param1, :param2, etc for PostgreSQL
        if params and '?' in query:
            converted_query = query
            param_dict = {}
            if isinstance(params, (list, tuple)):
                for i, param in enumerate(params):
                    placeholder = f':param{i}'
                    converted_query = converted_query.replace('?', placeholder, 1)
                    param_dict[f'param{i}'] = param
            else:
                param_dict = params
            
            # For INSERT queries without RETURNING, add RETURNING id to capture lastrowid
            if 'INSERT INTO' in converted_query.upper() and 'RETURNING' not in converted_query.upper():
                converted_query = converted_query.rstrip().rstrip(';') + ' RETURNING id'
            
            self._result = self.session.execute(text(converted_query), param_dict)
        else:
            # For non-parameterized queries
            converted_query = query
            if 'INSERT INTO' in converted_query.upper() and 'RETURNING' not in converted_query.upper():
                converted_query = converted_query.rstrip().rstrip(';') + ' RETURNING id'
            
            self._result = self.session.execute(text(converted_query), params or {})
        
        self.rowcount = self._result.rowcount if hasattr(self._result, 'rowcount') else 0
        
        # Capture lastrowid for INSERT operations
        if 'INSERT INTO' in query.upper():
            try:
                # Use a fresh fetch to avoid exhausting results if multiple rows (unlikely for our inserts)
                # For our simple inserts, one row is expected from RETURNING id
                row = self._result.fetchone()
                if row:
                    self.lastrowid = row[0]
                    # Since we consumed the row, we need to store it if someone calls fetchone()
                    self._first_row = row
                else:
                    self.lastrowid = None
                    self._first_row = None
            except:
                self.lastrowid = None
                self._first_row = None
        else:
            self.lastrowid = None
            self._first_row = None
        
        return self._result
    
    def executemany(self, query, params_list):
        # Convert ? to named parameters
        count = 0
        for params in params_list:
            converted_query = query
            param_dict = {}
            if isinstance(params, (list, tuple)):
                for i, param in enumerate(params):
                    placeholder = f':param{i}'
                    converted_query = converted_query.replace('?', placeholder, 1)
                    param_dict[f'param{i}'] = param
            else:
                param_dict = params
            
            # Note: Postgres doesn't like INSERT OR REPLACE, but SQLite does.
            # If we're on SQLite, we keep it. If we're on Postgres, we'd need to convert it.
            # For now, we assume the query is compatible or handled by the engine.
            self.session.execute(text(converted_query), param_dict)
            count += 1
        self.rowcount = count
    
    def fetchone(self):
        if hasattr(self, '_first_row') and self._first_row is not None:
            row = self._first_row
            self._first_row = None
            return RowProxy(self._result.keys(), row)
            
        if not self._result:
            return None
        row = self._result.fetchone()
        if row is None:
            return None
        return RowProxy(self._result.keys(), row)
    
    def fetchall(self):
        if not self._result:
            return []
        rows = self._result.fetchall()
        # Convert all rows to dict-like objects
        keys = self._result.keys()
        return [RowProxy(keys, row) for row in rows]


@contextmanager
def get_db():
    """
    Context manager for database sessions with SQLite compatibility.
    
    Returns a session with a cursor() method for backward compatibility.
    
    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items")
            rows = cursor.fetchall()
    """
    session = SessionLocal()
    
    # Add cursor() method to session for compatibility
    def cursor():
        return CursorWrapper(session)
    
    session.cursor = cursor
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize database with all required tables"""
    is_sqlite = 'sqlite' in str(engine.url)
    pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    
    logger.info(f"Initializing {'SQLite' if is_sqlite else 'PostgreSQL'} database...")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Accounts table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS accounts (
                id {pk_type},
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                password_hash TEXT
            )
        ''')
        
        # Migration: Add password_hash if missing
        try:
            if is_sqlite:
                cursor.execute("PRAGMA table_info(accounts)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'password_hash' not in columns:
                    logger.info("Migrating: Adding password_hash to accounts...")
                    cursor.execute("ALTER TABLE accounts ADD COLUMN password_hash TEXT")
            else:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='accounts' AND column_name='password_hash'
                """)
                if not cursor.fetchone():
                    logger.info("Migrating: Adding password_hash to accounts...")
                    cursor.execute("ALTER TABLE accounts ADD COLUMN password_hash TEXT")
            
            # Set default password for existing accounts
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE password_hash IS NULL")
            if cursor.fetchone()[0] > 0:
                from app.utils.security import get_password_hash
                default_hash = get_password_hash("password")
                logger.info("Setting default password 'password' for existing accounts...")
                cursor.execute("UPDATE accounts SET password_hash = ? WHERE password_hash IS NULL", (default_hash,))
                
        except Exception as e:
            logger.warning(f"Migration check failed (might be already up to date): {e}")

        # Items table
        # id is NOT autoincrement here because it's the OSRS item ID
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                examine TEXT,
                members BOOLEAN,
                lowalch INTEGER,
                highalch INTEGER,
                value INTEGER,
                ge_limit INTEGER,
                icon TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index on name
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)
        ''')
        
        # User flips table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS user_flips (
                id {pk_type},
                account_id INTEGER,
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity_total INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                buy_price INTEGER NOT NULL,
                sell_price INTEGER,
                intended_sell_price INTEGER,
                buy_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sell_time TIMESTAMP,
                profit INTEGER,
                roi REAL,
                status TEXT DEFAULT 'pending',
                cancel_reason TEXT,
                notes TEXT,
                intended_quantity INTEGER,
                buy_offer_started_at TIMESTAMP,
                last_buy_at TIMESTAMP,
                sell_offer_started_at TIMESTAMP,
                last_sell_at TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_flips_status ON user_flips(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_flips_item ON user_flips(item_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_flips_account ON user_flips(account_id)
        ''')
        
        # User settings table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS user_settings (
                id {pk_type},
                account_id INTEGER NOT NULL UNIQUE,
                available_cash BIGINT DEFAULT 0,
                profit_take_pct FLOAT DEFAULT 0,
                loss_refill_pct FLOAT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')
        
        # Flip transactions table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS flip_transactions (
                id {pk_type},
                flip_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                mutation_type TEXT,
                quantity INTEGER,
                price INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (flip_id) REFERENCES user_flips(id)
            )
        ''')
        
        # Price history table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS price_history (
                id {pk_type},
                item_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                price_high INTEGER,
                price_low INTEGER,
                volume_high INTEGER,
                volume_low INTEGER,
                UNIQUE(item_id, timestamp),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        ''')
        
        # Create index on item_id and timestamp for fast queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_item_time 
            ON price_history(item_id, timestamp DESC)
        ''')
        
        # Price polling metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_polling_metadata (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled BOOLEAN DEFAULT TRUE,
                last_poll_timestamp INTEGER,
                last_poll_time TIMESTAMP,
                total_snapshots INTEGER DEFAULT 0,
                last_item_sync_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Item conversions table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS item_conversions (
                id {pk_type},
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                conversion_rate_per_hour INTEGER,
                skill_required TEXT,
                level_required INTEGER,
                members BOOLEAN DEFAULT TRUE,
                wiki_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Conversion items table (for multiple inputs/outputs)
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS conversion_items (
                id {pk_type},
                conversion_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity REAL NOT NULL DEFAULT 1,
                is_input BOOLEAN NOT NULL,
                FOREIGN KEY (conversion_id) REFERENCES item_conversions(id)
            )
        ''')

        # Create indexes for conversions
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conv_items_cid ON conversion_items(conversion_id)
        ''')
        
        # Insert default metadata
        cursor.execute('''
            INSERT INTO price_polling_metadata (id, enabled) 
            VALUES (1, TRUE)
            ON CONFLICT (id) DO NOTHING
        ''')

        # Insert a default account if none exist
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding default 'Main' account...")
            cursor.execute("INSERT INTO accounts (name) VALUES ('Main')")
        
    logger.info("✅ Database initialized successfully!")


def test_connection():
    """Test database connection"""
    try:
        with get_db() as db:
            result = db.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


if __name__ == '__main__':
    # Test connection and initialize
    logging.basicConfig(level=logging.INFO)
    if test_connection():
        init_database()