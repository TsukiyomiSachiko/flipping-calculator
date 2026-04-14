"""
Data Compression Service

Periodically compresses old price history data to save space while maintaining trends.
Runs as a background task.

Logic:
- Runs once a day at midnight
- Identifies items with > 10,000 records
- Keeps last 7 days raw
- Compresses older data to ~1,000 points using dynamic grouping
- Aggregates: Avg Price, Sum Volume, Max Timestamp
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from sqlalchemy import text
from app.utils.database import get_db

logger = logging.getLogger(__name__)

class DataCompressionService:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._should_run = True
        self._last_run_date = None

    async def start(self):
        """Start the background compression task"""
        if self._task is not None and not self._task.done():
            return
        
        logger.info("Starting data compression service...")
        self._should_run = True
        self._task = asyncio.create_task(self._compression_loop())

    async def stop(self):
        """Stop the background compression task"""
        logger.info("Stopping data compression service...")
        self._should_run = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _compression_loop(self):
        """Main loop that checks for midnight execution"""
        while self._should_run:
            try:
                now = datetime.now(timezone.utc)
                
                # Check if we should run (Midnight UTC and haven't run today)
                if now.hour == 0 and (self._last_run_date != now.date()):
                    logger.info("🕛 Midnight Trigger: Starting Daily Data Compression...")
                    await self._compress_data()
                    self._last_run_date = now.date()
                    logger.info("✅ Daily Data Compression Complete.")
                
                # Check every minute
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in compression loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _compress_data(self):
        """Execute the compression logic"""
        try:
            # 1. Identify candidates
            candidates = self._get_candidates()
            if not candidates:
                logger.info("No items require compression.")
                return

            logger.info(f"Found {len(candidates)} items with > 10,000 records.")

            # 2. Process each candidate
            for item_id, count in candidates:
                if not self._should_run: break
                
                await self._process_item(item_id)
                # Brief yield to let other tasks run
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Compression failed: {e}", exc_info=True)

    def _get_candidates(self) -> List[tuple]:
        """Find items with > 10,000 records"""
        with get_db() as session:
            result = session.execute(text('''
                SELECT item_id, COUNT(*) as count 
                FROM price_history 
                GROUP BY item_id 
                HAVING COUNT(*) > 10000
            '''))
            return [(row[0], row[1]) for row in result.fetchall()]

    async def _process_item(self, item_id: int):
        """Compress data for a single item"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        with get_db() as session:
            # Get records older than 7 days
            result = session.execute(text('''
                SELECT id, timestamp, price_high, price_low, volume_high, volume_low 
                FROM price_history 
                WHERE item_id = :item_id AND timestamp < :cutoff 
                ORDER BY timestamp ASC
            '''), {'item_id': item_id, 'cutoff': cutoff_date})
            
            # Map RowProxy/Tuple to dict for easier handling
            rows = []
            for r in result.fetchall():
                # Handle RowProxy (access by key) or tuple (access by index)
                if hasattr(r, '_mapping'): # SQLAlchemy 1.4+ Row
                    d = dict(r._mapping)
                elif hasattr(r, 'keys'): # Legacy/Custom RowProxy
                    d = dict(r)
                else: # Tuple fallback (assuming order)
                    d = {
                        'id': r[0], 'timestamp': r[1], 
                        'price_high': r[2], 'price_low': r[3], 
                        'volume_high': r[4], 'volume_low': r[5]
                    }
                rows.append(d)

            count = len(rows)
            if count <= 1000:
                return # Not enough old data to compress

            # Dynamic Group Size
            target_count = 1000
            group_size = math.ceil(count / target_count)
            
            logger.info(f"Compressing item {item_id}: {count} old records -> ~{target_count} (Group size: {group_size})")

            new_records = []
            ids_to_delete = []

            # Chunk data
            for i in range(0, count, group_size):
                chunk = rows[i:i + group_size]
                if not chunk: continue

                # Aggregate
                # Prices: Average (ignore None)
                highs = [r['price_high'] for r in chunk if r['price_high'] is not None]
                lows = [r['price_low'] for r in chunk if r['price_low'] is not None]
                
                avg_high = int(sum(highs) / len(highs)) if highs else None
                avg_low = int(sum(lows) / len(lows)) if lows else None
                
                # Volume: Sum
                sum_vol_high = sum(r['volume_high'] or 0 for r in chunk)
                sum_vol_low = sum(r['volume_low'] or 0 for r in chunk)
                
                # Timestamp: Latest in chunk
                max_ts = chunk[-1]['timestamp']

                new_records.append({
                    'item_id': item_id,
                    'timestamp': max_ts,
                    'price_high': avg_high,
                    'price_low': avg_low,
                    'volume_high': sum_vol_high,
                    'volume_low': sum_vol_low
                })
                
                ids_to_delete.extend([r['id'] for r in chunk])

            # Transactional Swap
            try:
                # 1. Delete old records using batch delete
                # Chunk deletions to avoid statement limits if massive
                del_chunk_size = 1000
                for i in range(0, len(ids_to_delete), del_chunk_size):
                    chunk_ids = tuple(ids_to_delete[i:i + del_chunk_size])
                    if not chunk_ids: continue
                    
                    # Manual formatting for IN clause to support tuple with 1 element
                    # (1,) string representation is "(1,)" which is valid SQL
                    session.execute(text(f"DELETE FROM price_history WHERE id IN {chunk_ids}"))

                # 2. Insert new aggregated records
                session.execute(text('''
                    INSERT INTO price_history 
                    (item_id, timestamp, price_high, price_low, volume_high, volume_low)
                    VALUES (:item_id, :timestamp, :price_high, :price_low, :volume_high, :volume_low)
                    ON CONFLICT (item_id, timestamp) DO UPDATE SET
                        price_high = EXCLUDED.price_high,
                        price_low = EXCLUDED.price_low,
                        volume_high = EXCLUDED.volume_high,
                        volume_low = EXCLUDED.volume_low
                '''), new_records)
                
                session.commit()
                logger.info(f"Item {item_id}: Compression successful. Removed {len(ids_to_delete)}, Added {len(new_records)}.")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Item {item_id}: DB Error during swap: {e}")

# Global instance
data_compression_service = DataCompressionService()
