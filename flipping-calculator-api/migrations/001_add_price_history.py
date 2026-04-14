#!/usr/bin/env python3
"""
Migration: Add price_history table

This migration adds a new table to store historical price data collected
from the OSRS Wiki API. This allows the app to build its own timeseries
database instead of relying on the Wiki's /timeseries endpoint.

Table structure:
- item_id: The OSRS item ID
- timestamp: Unix timestamp of the price snapshot
- high_price: Average high (instant buy) price
- low_price: Average low (instant sell) price  
- high_volume: Trading volume on high side
- low_volume: Trading volume on low side
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.database import DB_PATH

def run_migration():
    """Execute the migration"""
    print(f"Running migration: Add price_history table")
    print(f"Database path: {DB_PATH}")
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='price_history'
        """)
        
        if cursor.fetchone():
            print("⚠️  Table 'price_history' already exists, skipping creation")
        else:
            # Create price_history table
            print("Creating price_history table...")
            cursor.execute('''
                CREATE TABLE price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    high_price INTEGER,
                    low_price INTEGER,
                    high_volume INTEGER,
                    low_volume INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id),
                    UNIQUE(item_id, timestamp)
                )
            ''')
            print("✓ Table created")
            
            # Create indexes for efficient querying
            print("Creating indexes...")
            cursor.execute('''
                CREATE INDEX idx_price_history_item_time 
                ON price_history(item_id, timestamp DESC)
            ''')
            cursor.execute('''
                CREATE INDEX idx_price_history_timestamp 
                ON price_history(timestamp DESC)
            ''')
            print("✓ Indexes created")
        
        # Create metadata table to track polling status
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='price_polling_metadata'
        """)
        
        if cursor.fetchone():
            print("⚠️  Table 'price_polling_metadata' already exists, skipping creation")
        else:
            print("Creating price_polling_metadata table...")
            cursor.execute('''
                CREATE TABLE price_polling_metadata (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_poll_timestamp INTEGER,
                    last_poll_time TIMESTAMP,
                    total_snapshots INTEGER DEFAULT 0,
                    polling_enabled BOOLEAN DEFAULT 1,
                    poll_interval_minutes INTEGER DEFAULT 5
                )
            ''')
            
            # Insert initial metadata row
            cursor.execute('''
                INSERT INTO price_polling_metadata 
                (id, last_poll_timestamp, total_snapshots, polling_enabled, poll_interval_minutes)
                VALUES (1, 0, 0, 1, 5)
            ''')
            print("✓ Metadata table created")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Print summary
        cursor.execute("SELECT COUNT(*) as count FROM price_history")
        count = cursor.fetchone()[0]
        print(f"\nCurrent state:")
        print(f"  - price_history records: {count}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def rollback_migration():
    """Rollback the migration (for testing)"""
    print(f"Rolling back migration: Add price_history table")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Dropping tables...")
        cursor.execute("DROP TABLE IF EXISTS price_history")
        cursor.execute("DROP TABLE IF EXISTS price_polling_metadata")
        conn.commit()
        print("✅ Rollback completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback_migration()
    else:
        run_migration()
