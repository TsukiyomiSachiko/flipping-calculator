"""
Migration: Add fill rate tracking timestamps to user_flips

Adds timestamp columns for monitoring buy/sell offer fill rates:
- buy_offer_started_at: When buy offer was first placed
- last_buy_at: Most recent buy activity
- sell_offer_started_at: When first item entered inventory
- last_sell_at: Most recent sell activity

Run: python migrations/006_add_fill_rate_timestamps.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import get_db
from datetime import datetime


def migrate():
    """Add fill rate tracking timestamp columns to user_flips table"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        columns_to_add = [
            'buy_offer_started_at',
            'last_buy_at',
            'sell_offer_started_at',
            'last_sell_at'
        ]
        
        # Check which columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_flips' 
            AND column_name IN ('buy_offer_started_at', 'last_buy_at', 'sell_offer_started_at', 'last_sell_at')
        """)
        
        existing_columns = [row['column_name'] for row in cursor.fetchall()]
        columns_needed = [col for col in columns_to_add if col not in existing_columns]
        
        if not columns_needed:
            print("✓ All fill rate timestamp columns already exist")
            return
        
        print("Adding fill rate tracking columns to user_flips...")
        
        # Add missing columns
        for column in columns_needed:
            print(f"  - Adding {column}...")
            cursor.execute(f"""
                ALTER TABLE user_flips 
                ADD COLUMN {column} TIMESTAMP
            """)
        
        # Backfill data for existing flips
        print("\nBackfilling timestamp data for existing flips...")
        
        # Backfill buy_offer_started_at and last_buy_at from buy_time
        cursor.execute("""
            UPDATE user_flips 
            SET buy_offer_started_at = buy_time, 
                last_buy_at = buy_time
            WHERE buy_offer_started_at IS NULL AND buy_time IS NOT NULL
        """)
        buy_backfilled = cursor.rowcount
        print(f"  - Backfilled {buy_backfilled} buy timestamps")
        
        # Backfill sell_offer_started_at and last_sell_at for completed flips
        cursor.execute("""
            UPDATE user_flips 
            SET sell_offer_started_at = sell_time,
                last_sell_at = sell_time
            WHERE sell_offer_started_at IS NULL 
              AND sell_time IS NOT NULL 
              AND status = 'completed'
        """)
        sell_completed = cursor.rowcount
        print(f"  - Backfilled {sell_completed} completed sell timestamps")
        
        # For partially completed flips with inventory, estimate sell_offer_started_at
        cursor.execute("""
            UPDATE user_flips
            SET sell_offer_started_at = buy_time
            WHERE sell_offer_started_at IS NULL 
              AND quantity_remaining > 0 
              AND quantity_remaining < quantity_total
              AND buy_time IS NOT NULL
        """)
        sell_partial = cursor.rowcount
        print(f"  - Backfilled {sell_partial} partial flip sell start timestamps")
        
        conn.commit()
        print("\n✓ Migration complete!")
        print("  Columns added:")
        for col in columns_needed:
            print(f"    - {col}")
        print("\n  Fill rate monitoring is now active!")


if __name__ == "__main__":
    migrate()
