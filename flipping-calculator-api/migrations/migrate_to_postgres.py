"""
Migrate data from SQLite to PostgreSQL

Copies all data from the existing SQLite database to PostgreSQL.
"""

import sqlite3
import logging
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.utils.database import get_db, init_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLITE_PATH = 'data/osrs_flipping.db'


def migrate_table(sqlite_conn, table_name, pg_session):
    """Migrate a single table from SQLite to PostgreSQL"""
    cursor = sqlite_conn.cursor()
    
    # Get all rows
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    
    if not rows:
        logger.info(f"  {table_name}: No data to migrate")
        return 0
    
    # Get column names
    columns = [description[0] for description in cursor.description]
    
    # Column name mapping (SQLite -> PostgreSQL)
    column_mapping = {
        'high_price': 'price_high',
        'low_price': 'price_low',
        'high_volume': 'volume_high',
        'low_volume': 'volume_low',
        'created_at': 'timestamp'  # SQLite has created_at, PostgreSQL uses timestamp
    }
    
    # Map column names for PostgreSQL
    pg_columns = [column_mapping.get(col, col) for col in columns]
    
    # Remove created_at if it exists (we use timestamp instead)
    if 'created_at' in columns and table_name == 'price_history':
        # Don't include created_at in the insert, we already have timestamp
        columns_to_use = [col for col in columns if col != 'created_at']
        pg_columns_to_use = [column_mapping.get(col, col) for col in columns_to_use]
    else:
        columns_to_use = columns
        pg_columns_to_use = pg_columns
    
    # Build insert query
    placeholders = ', '.join([f':{col}' for col in columns_to_use])
    cols_str = ', '.join(pg_columns_to_use)
    
    # Special handling for different tables
    if table_name == 'user_flips':
        # PostgreSQL uses SERIAL for auto-increment
        insert_query = f'''
            INSERT INTO {table_name} ({cols_str})
            VALUES ({placeholders})
        '''
    else:
        insert_query = f'''
            INSERT INTO {table_name} ({cols_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        '''
    
    # Insert rows
    count = 0
    skipped = 0
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns_to_use):
            row_dict[col] = row[columns.index(col)]
        
        # Convert SQLite boolean integers to PostgreSQL booleans
        if table_name == 'items' and 'members' in row_dict:
            row_dict['members'] = bool(row_dict['members'])
        
        # Convert Unix timestamp to datetime for price_history
        if table_name == 'price_history' and 'timestamp' in row_dict:
            from datetime import datetime as dt
            row_dict['timestamp'] = dt.fromtimestamp(row_dict['timestamp'])
        
        try:
            pg_session.execute(text(insert_query), row_dict)
            count += 1
            # Commit after each successful insert to avoid losing data on rollback
            pg_session.commit()
        except Exception as e:
            # Skip orphaned records (foreign key violations)
            error_str = str(e)
            if 'ForeignKeyViolation' in error_str or 'violates foreign key constraint' in error_str:
                skipped += 1
                # Rollback just this failed transaction
                pg_session.rollback()
            else:
                raise
    
    if skipped > 0:
        logger.info(f"  {table_name}: Migrated {count} rows (skipped {skipped} orphaned records)")
    else:
        logger.info(f"  {table_name}: Migrated {count} rows")
    
    return count


def migrate_all():
    """Migrate all data from SQLite to PostgreSQL"""
    logger.info("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # Initialize PostgreSQL database
    logger.info("📦 Initializing PostgreSQL database...")
    init_database()
    
    # Connect to SQLite
    logger.info("📂 Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Get PostgreSQL session
    with get_db() as pg_session:
        # Migrate tables in order (respecting foreign keys)
        tables = [
            'items',
            'user_settings',
            'user_flips',
            'flip_transactions',
            'price_history'
        ]
        
        total_rows = 0
        for table in tables:
            try:
                count = migrate_table(sqlite_conn, table, pg_session)
                total_rows += count
            except Exception as e:
                logger.error(f"❌ Error migrating {table}: {e}")
                raise
        
        # Reset sequences for SERIAL columns
        logger.info("🔢 Resetting sequences...")
        pg_session.execute(text('''
            SELECT setval('user_flips_id_seq', 
                COALESCE((SELECT MAX(id) FROM user_flips), 1))
        '''))
        pg_session.execute(text('''
            SELECT setval('flip_transactions_id_seq', 
                COALESCE((SELECT MAX(id) FROM flip_transactions), 1))
        '''))
        pg_session.execute(text('''
            SELECT setval('price_history_id_seq', 
                COALESCE((SELECT MAX(id) FROM price_history), 1))
        '''))
    
    sqlite_conn.close()
    
    logger.info(f"✅ Migration complete! Migrated {total_rows} total rows")
    logger.info("")
    logger.info("📝 Next steps:")
    logger.info("1. Backup your SQLite database (data/osrs_flipping.db)")
    logger.info("2. Update app/utils/database.py to import from database_postgres")
    logger.info("3. Restart the API server")


if __name__ == '__main__':
    migrate_all()