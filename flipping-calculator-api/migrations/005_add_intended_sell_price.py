"""
Migration: Add intended_sell_price to user_flips

Adds intended_sell_price column to store the target sell price captured at buy time.
This allows users to remember what price they intended to sell at.

Run: python migrations/add_intended_sell_price.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import get_db


def migrate():
    """Add intended_sell_price column to user_flips table"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_flips' 
            AND column_name = 'intended_sell_price'
        """)
        
        if cursor.fetchone():
            print("✓ Column 'intended_sell_price' already exists")
            return
        
        print("Adding 'intended_sell_price' column to user_flips...")
        cursor.execute("""
            ALTER TABLE user_flips 
            ADD COLUMN intended_sell_price INTEGER
        """)
        
        conn.commit()
        print("✓ Migration complete!")
        print("  - Added intended_sell_price column (stores target sell price at buy time)")


if __name__ == "__main__":
    migrate()
