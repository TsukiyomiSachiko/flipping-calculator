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

def execute_query(session, query: str, params=None):
    if not params:
        if 'INSERT INTO' in query.upper() and 'RETURNING' not in query.upper():
            query = query.rstrip().rstrip(';') + ' RETURNING id'
        return session.execute(text(query))

    converted_query = query
    param_dict = {}
    
    if isinstance(params, (list, tuple)):
        for i, param in enumerate(params):
            placeholder = f':param{i}'
            converted_query = converted_query.replace('?', placeholder, 1)
            param_dict[f'param{i}'] = param
    elif isinstance(params, dict):
        param_dict = params
    
    if 'INSERT INTO' in converted_query.upper() and 'RETURNING' not in converted_query.upper():
        converted_query = converted_query.rstrip().rstrip(';') + ' RETURNING id'

    return session.execute(text(converted_query), param_dict)


def executemany_query(session, query: str, params_list):
    if not params_list:
        return
        
    converted_query = query
    if isinstance(params_list[0], (list, tuple)):
        for i in range(len(params_list[0])):
            placeholder = f':param{i}'
            converted_query = converted_query.replace('?', placeholder, 1)
            
        dict_params_list = []
        for params in params_list:
            param_dict = {f'param{i}': p for i, p in enumerate(params)}
            dict_params_list.append(param_dict)
            
        return session.execute(text(converted_query), dict_params_list)
    else:
         return session.execute(text(converted_query), params_list)



@contextmanager
def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def init_database():
    pk_type = "SERIAL PRIMARY KEY"
    logger.info("Initializing PostgreSQL database...")
    
    with get_db() as session:
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                password_hash TEXT
            )
        '''))
        
        # Migration: Add password_hash if missing
        try:
            result = session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='accounts' AND column_name='password_hash'
            """))
            if not result.fetchone():
                logger.info("Migrating: Adding password_hash to accounts...")
                session.execute(text("ALTER TABLE accounts ADD COLUMN password_hash TEXT"))
            
            # Set default password for existing accounts
            result = session.execute(text("SELECT COUNT(*) FROM accounts WHERE password_hash IS NULL"))
            if result.fetchone()[0] > 0:
                from app.utils.security import get_password_hash
                default_hash = get_password_hash("password")
                logger.info("Setting default password 'password' for existing accounts...")
                execute_query(session, "UPDATE accounts SET password_hash = ? WHERE password_hash IS NULL", (default_hash,))
                
        except Exception as e:
            logger.warning(f"Migration check failed (might be already up to date): {e}")

        session.execute(text('''
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
        '''))
        
        session.execute(text('CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)'))
        
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS user_flips (
                id SERIAL PRIMARY KEY,
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
        '''))
        
        session.execute(text('CREATE INDEX IF NOT EXISTS idx_flips_status ON user_flips(status)'))
        session.execute(text('CREATE INDEX IF NOT EXISTS idx_flips_item ON user_flips(item_id)'))
        session.execute(text('CREATE INDEX IF NOT EXISTS idx_flips_account ON user_flips(account_id)'))
        
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id SERIAL PRIMARY KEY,
                account_id INTEGER NOT NULL UNIQUE,
                available_cash BIGINT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        '''))
        
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS flip_transactions (
                id SERIAL PRIMARY KEY,
                flip_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                mutation_type TEXT,
                quantity INTEGER,
                price INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (flip_id) REFERENCES user_flips(id)
            )
        '''))
        
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                item_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                price_high INTEGER,
                price_low INTEGER,
                volume_high INTEGER,
                volume_low INTEGER,
                UNIQUE(item_id, timestamp),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        '''))
        
        session.execute(text('CREATE INDEX IF NOT EXISTS idx_price_history_item_time ON price_history(item_id, timestamp DESC)'))
        
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS price_polling_metadata (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled BOOLEAN DEFAULT TRUE,
                last_poll_timestamp INTEGER,
                last_poll_time TIMESTAMP,
                total_snapshots INTEGER DEFAULT 0,
                last_item_sync_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))

        session.execute(text('''
            CREATE TABLE IF NOT EXISTS item_conversions (
                id SERIAL PRIMARY KEY,
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
        '''))

        session.execute(text('''
            CREATE TABLE IF NOT EXISTS conversion_items (
                id SERIAL PRIMARY KEY,
                conversion_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity REAL NOT NULL DEFAULT 1,
                is_input BOOLEAN NOT NULL,
                FOREIGN KEY (conversion_id) REFERENCES item_conversions(id)
            )
        '''))

        session.execute(text('CREATE INDEX IF NOT EXISTS idx_conv_items_cid ON conversion_items(conversion_id)'))
        
        session.execute(text('''
            INSERT INTO price_polling_metadata (id, enabled) 
            VALUES (1, TRUE)
            ON CONFLICT (id) DO NOTHING
        '''))

        result = session.execute(text("SELECT COUNT(*) FROM accounts"))
        if result.fetchone()[0] == 0:
            logger.info("Seeding default 'Main' account...")
            session.execute(text("INSERT INTO accounts (name) VALUES ('Main')"))
        
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
