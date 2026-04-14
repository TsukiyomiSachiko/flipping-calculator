"""
Migration: Add user_settings table for tracking available cash

Run with: python migrations/add_user_settings.py
"""

import sqlite3
import os

DB_PATH = 'data/osrs_flipping.db'

def migrate():
    """Add user_settings table"""
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create user_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            available_cash INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default row if doesn't exist
    cursor.execute('''
        INSERT OR IGNORE INTO user_settings (id, available_cash) 
        VALUES (1, 0)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Migration complete: user_settings table created")
    print("   - available_cash tracking enabled")
    print("   - Default cash: 0 gp (update via API)")

if __name__ == '__main__':
    migrate()
