"""
Sync missing items from OSRS Wiki API.
"""
import logging
from app.services.item_service import ItemService
from app.utils.api_client import fetch_item_mapping
from app.utils.database import get_db
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync():
    logger.info("Fetching item mapping from Wiki...")
    item_data = fetch_item_mapping(use_cache=False)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get existing IDs
        cursor.execute("SELECT id FROM items")
        existing_ids = {row['id'] for row in cursor.fetchall()}
        
        missing_items = [item for item in item_data if item['id'] not in existing_ids]
        
        if not missing_items:
            logger.info("No missing items found.")
            return

        logger.info(f"Found {len(missing_items)} missing items. Inserting...")
        
        items_to_insert = []
        for item in missing_items:
            items_to_insert.append((
                item['id'],
                item['name'],
                item.get('examine'),
                item.get('members', False),
                item.get('lowalch'),
                item.get('highalch'),
                item.get('value'),
                item.get('limit', 0),
                item.get('icon'),
                datetime.now()
            ))
            
        cursor.executemany('''
            INSERT INTO items 
            (id, name, examine, members, lowalch, highalch, value, ge_limit, icon, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING
        ''', items_to_insert)
        
        conn.commit()
        logger.info(f"✅ Successfully added {len(items_to_insert)} missing items.")

if __name__ == "__main__":
    sync()
