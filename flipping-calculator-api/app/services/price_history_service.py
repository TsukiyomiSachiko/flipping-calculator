"""
Price History Service

Manages the local price history database. Provides methods to:
- Save price snapshots from API polling
- Query historical data for items
- Build custom timeseries from stored data
- Replace dependency on Wiki's /timeseries endpoint
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import logging
from app.utils.database import get_db, execute_query, executemany_query

logger = logging.getLogger(__name__)


class PriceHistoryService:
    """Service for managing local price history storage"""
    
    @staticmethod
    def save_price_snapshot(item_data: Dict[str, Dict], max_retries: int = 3) -> int:
        """
        Save a batch of price snapshots from /latest or /5m endpoint.
        Optimized to use bulk inserts, falling back to row-by-row on failure.
        """
        if not item_data:
            return 0
        
        current_timestamp = datetime.now(timezone.utc).replace(microsecond=0)
        inserted_count = 0
        
        # Prepare data for bulk insert
        records_to_insert = []
        
        # First pass: validate and prepare all records
        # We need a session to check valid IDs
        with get_db() as session:
            try:
                result = session.execute(text("SELECT id FROM items"))
                valid_item_ids = {row[0] for row in result.fetchall()}
            except Exception as e:
                logger.error(f"Failed to fetch valid item IDs: {e}")
                return 0

        for item_id_str, data in item_data.items():
            try:
                item_id = int(item_id_str)
                
                if item_id not in valid_item_ids:
                    continue
                
                price_high = data.get('high', data.get('avgHighPrice'))
                price_low = data.get('low', data.get('avgLowPrice'))
                
                if price_high is None and price_low is None:
                    continue
                
                timestamp_val = data.get('highTime', data.get('lowTime'))
                if timestamp_val:
                    timestamp = datetime.fromtimestamp(timestamp_val, tz=timezone.utc).replace(tzinfo=None)
                else:
                    timestamp = current_timestamp.replace(tzinfo=None)
                
                volume_high = data.get('highPriceVolume', 0)
                volume_low = data.get('lowPriceVolume', 0)
                
                records_to_insert.append({
                    'item_id': item_id,
                    'timestamp': timestamp,
                    'price_high': price_high,
                    'price_low': price_low,
                    'volume_high': volume_high,
                    'volume_low': volume_low
                })
            except Exception:
                continue
        
        if not records_to_insert:
            return 0

        # Attempt bulk insert
        for attempt in range(max_retries):
            try:
                with get_db() as session:
                    # We use ON CONFLICT DO NOTHING to handle duplicates gracefully during bulk insert
                    # Note: We don't get 'inserted_count' easily with executemany + ON CONFLICT in generic SQL
                    # But for performance, we assume if it succeeds, we processed them.
                    session.execute(text('''
                        INSERT INTO price_history 
                        (item_id, timestamp, price_high, price_low, volume_high, volume_low)
                        VALUES (:item_id, :timestamp, :price_high, :price_low, :volume_high, :volume_low)
                        ON CONFLICT (item_id, timestamp) DO NOTHING
                    '''), records_to_insert)
                    
                    inserted_count = len(records_to_insert) # Approximate, includes ignored duplicates
                    session.commit()
                    break # Success!
                    
            except Exception as e:
                logger.error(f"Bulk insert failed (attempt {attempt+1}/{max_retries}): {e}")
                
                # If we're on the last attempt or it's a data error, fall back to row-by-row
                if attempt == max_retries - 1:
                    logger.warning("Falling back to row-by-row insertion...")
                    inserted_count = 0
                    with get_db() as session:
                        for record in records_to_insert:
                            try:
                                # Use nested transaction for isolation
                                session.begin_nested()
                                result = session.execute(text('''
                                    INSERT INTO price_history 
                                    (item_id, timestamp, price_high, price_low, volume_high, volume_low)
                                    VALUES (:item_id, :timestamp, :price_high, :price_low, :volume_high, :volume_low)
                                    ON CONFLICT (item_id, timestamp) DO NOTHING
                                '''), record)
                                inserted_count += 1
                                session.commit()
                            except Exception as inner_e:
                                session.rollback()
                                logger.error(f"Failed to insert record for item {record['item_id']}: {inner_e}")
                    # After row-by-row, we consider it 'done' despite partial failures
                    break
                
                import time
                time.sleep(1)

        # Update metadata
        try:
            with get_db() as session:
                session.execute(text('''
                    UPDATE price_polling_metadata 
                    SET last_poll_timestamp = :ts_val,
                        last_poll_time = :ts_dt,
                        total_snapshots = total_snapshots + :count
                    WHERE id = 1
                '''), {
                    'ts_val': int(current_timestamp.timestamp()),
                    'ts_dt': current_timestamp.replace(tzinfo=None),
                    'count': inserted_count
                })
                session.commit()
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            
        return inserted_count
    
    @staticmethod
    def get_item_history(
        item_id: int,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve price history for a specific item
        
        Args:
            item_id: The item ID
            hours: How many hours of history to retrieve (default 24)
            limit: Maximum number of records to return
        
        Returns:
            List of price snapshots, newest first
        """
        cutoff_datetime = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with get_db() as session:
            
            query = '''
                SELECT item_id, timestamp, price_high, price_low, volume_high, volume_low
                FROM price_history
                WHERE item_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            _res = execute_query(session, query, (item_id, cutoff_datetime))
            rows = _res.mappings().fetchall()
            
            return [
                {
                    'item_id': row['item_id'],
                    'timestamp': row['timestamp'],
                    'price_high': row['price_high'],
                    'price_low': row['price_low'],
                    'volume_high': row['volume_high'],
                    'volume_low': row['volume_low'],
                }
                for row in rows
            ]
    
    @staticmethod
    def get_timeseries(
        item_id: int,
        timestep: str = '5m',
        hours: int = 24
    ) -> Dict:
        """
        Build a timeseries aggregation from stored price data
        Mimics the structure of the Wiki's /timeseries endpoint
        
        Args:
            item_id: The item ID
            timestep: Aggregation interval ('5m', '1h', '6h')
            hours: How many hours of history to include
        
        Returns:
            Dict with 'data' key containing list of aggregated snapshots
        """
        # Map timestep to interval in seconds
        interval_seconds = {
            '5m': 5 * 60,
            '1h': 60 * 60,
            '6h': 6 * 60 * 60,
        }.get(timestep, 5 * 60)
        
        raw_data = PriceHistoryService.get_item_history(item_id, hours=hours)
        
        if not raw_data:
            return {'data': []}
        
        # Group data into time buckets
        buckets = {}
        
        for snapshot in raw_data:
            # Calculate which bucket this timestamp belongs to
            bucket_timestamp = (snapshot['timestamp'] // interval_seconds) * interval_seconds
            
            if bucket_timestamp not in buckets:
                buckets[bucket_timestamp] = {
                    'price_highs': [],
                    'price_lows': [],
                    'volume_highs': [],
                    'volume_lows': [],
                }
            
            if snapshot['price_high'] is not None:
                buckets[bucket_timestamp]['price_highs'].append(snapshot['price_high'])
            if snapshot['price_low'] is not None:
                buckets[bucket_timestamp]['price_lows'].append(snapshot['price_low'])
            if snapshot['volume_high']:
                buckets[bucket_timestamp]['volume_highs'].append(snapshot['volume_high'])
            if snapshot['volume_low']:
                buckets[bucket_timestamp]['volume_lows'].append(snapshot['volume_low'])
        
        # Calculate averages for each bucket
        aggregated = []
        for timestamp in sorted(buckets.keys()):
            bucket = buckets[timestamp]
            
            avg_high = int(sum(bucket['price_highs']) / len(bucket['price_highs'])) if bucket['price_highs'] else None
            avg_low = int(sum(bucket['price_lows']) / len(bucket['price_lows'])) if bucket['price_lows'] else None
            total_high_vol = sum(bucket['volume_highs']) if bucket['volume_highs'] else 0
            total_low_vol = sum(bucket['volume_lows']) if bucket['volume_lows'] else 0
            
            aggregated.append({
                'timestamp': timestamp,
                'avgHighPrice': avg_high,
                'avgLowPrice': avg_low,
                'highPriceVolume': total_high_vol,
                'lowPriceVolume': total_low_vol,
            })
        
        return {'data': aggregated}
    
    @staticmethod
    def get_polling_metadata() -> Dict:
        """Get information about the polling system status"""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM price_polling_metadata WHERE id = 1')
            row = _res.mappings().fetchone()
            
            if not row:
                return {
                    'last_poll_timestamp': 0,
                    'last_poll_time': None,
                    'total_snapshots': 0,
                    'polling_enabled': True,
                    'poll_interval_minutes': 5,
                }
            
            return {
                'last_poll_timestamp': row['last_poll_timestamp'] or 0,
                'last_poll_time': row['last_poll_time'],
                'total_snapshots': row['total_snapshots'] or 0,
                'polling_enabled': bool(row['enabled']),  # Column is 'enabled' not 'polling_enabled'
                'poll_interval_minutes': 5,  # Hardcoded default, not stored in DB
            }
    
    @staticmethod
    def set_polling_enabled(enabled: bool):
        """Enable or disable automatic price polling"""
        with get_db() as session:
            _res = execute_query(session, '''
                UPDATE price_polling_metadata
                SET enabled = ?
                WHERE id = 1
            ''', (1 if enabled else 0,))
            session.commit()
        
        logger.info(f"Price polling {'enabled' if enabled else 'disabled'}")
    
    @staticmethod
    def get_database_stats() -> Dict:
        """Get statistics about the price history database"""
        with get_db() as session:
            
            # Total records
            _res = execute_query(session, 'SELECT COUNT(*) as total FROM price_history')
            total_records = _res.mappings().fetchone()['total']
            
            # Unique items tracked
            _res = execute_query(session, 'SELECT COUNT(DISTINCT item_id) as items FROM price_history')
            unique_items = _res.mappings().fetchone()['items']
            
            # Oldest and newest timestamps
            _res = execute_query(session, 'SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM price_history')
            row = _res.mappings().fetchone()
            oldest_dt = row['oldest']  # Already a datetime object from PostgreSQL
            newest_dt = row['newest']  # Already a datetime object from PostgreSQL
            
            # Calculate range in hours
            date_range_hours = 0
            if oldest_dt and newest_dt:
                date_range_hours = (newest_dt - oldest_dt).total_seconds() / 3600
            
            return {
                'total_records': total_records,
                'unique_items': unique_items,
                'oldest_timestamp': oldest_dt.timestamp() if oldest_dt else None,
                'newest_timestamp': newest_dt.timestamp() if newest_dt else None,
                'oldest_date': oldest_dt.isoformat() if oldest_dt else None,
                'newest_date': newest_dt.isoformat() if newest_dt else None,
                'date_range_hours': date_range_hours,
            }
    
    @staticmethod
    def cleanup_old_data(days_to_keep: int = 30) -> int:
        """
        Remove price history data older than specified days
        
        Args:
            days_to_keep: Number of days of history to retain (default 30)
        
        Returns:
            Number of records deleted
        """
        cutoff_datetime = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        with get_db() as session:
            _res = execute_query(session, 'DELETE FROM price_history WHERE timestamp < ?', (cutoff_datetime,))
            deleted = _res.rowcount
            session.commit()
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old price records (kept last {days_to_keep} days)")
        
        return deleted