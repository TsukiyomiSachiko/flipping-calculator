"""
Migration: Add intended_quantity to user_flips table

This allows users to set a target quantity they intend to buy,
then prevents adding more buys once that quantity is reached.
Helps prevent mistakes and provides better UX for partial fills.

Date: 2026-02-08
"""

import sqlite3
import os

DB_PATH = 'data/osrs_flipping.db'

def migrate():
    """Add intended_quantity column to user_flips table"""
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user_flips)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'intended_quantity' in columns:
            print("✓ Column 'intended_quantity' already exists")
            return
        
        # Add the new column
        cursor.execute('''
            ALTER TABLE user_flips 
            ADD COLUMN intended_quantity INTEGER
        ''')
        
        # Set intended_quantity = quantity_total for existing flips
        # (assume they got what they intended on first buy)
        cursor.execute('''
            UPDATE user_flips 
            SET intended_quantity = quantity_total 
            WHERE intended_quantity IS NULL
        ''')
        
        conn.commit()
        print("✓ Successfully added 'intended_quantity' column")
        print("✓ Set intended_quantity = quantity_total for existing flips")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
