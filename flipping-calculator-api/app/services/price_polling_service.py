"""
Background Price Polling Service

Periodically fetches price data from OSRS Wiki API and saves it to the local database.
Runs as a background task in FastAPI using asyncio.

Features:
- Configurable polling interval (default 5 minutes)
- Uses /5m endpoint for freshest data with volume
- Respects API rate limits (10 requests per 5 minutes)
- Can be enabled/disabled via API
- Automatic cleanup of old data (configurable retention)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.utils.api_client import fetch_5m_volume_data, fetch_latest_prices
from app.services.price_history_service import PriceHistoryService
from app.services.item_service import ItemService
from app.utils.database import get_db

logger = logging.getLogger(__name__)


class PricePollingService:
    """Background service that polls price data and saves it locally"""
    
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._should_run = True
        self._poll_interval_seconds = 300  # 5 minutes default
    
    async def start(self):
        """Start the background polling task"""
        if self._task is not None and not self._task.done():
            logger.warning("Price polling service already running")
            return
        
        logger.info("Starting price polling service...")
        self._should_run = True
        self._task = asyncio.create_task(self._polling_loop())
    
    async def stop(self):
        """Stop the background polling task"""
        logger.info("Stopping price polling service...")
        self._should_run = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Price polling service stopped")
    
    async def _polling_loop(self):
        """Main polling loop that runs continuously"""
        # Wait a bit before first poll to allow app to fully start
        await asyncio.sleep(10)
        
        while self._should_run:
            try:
                # Check if polling is enabled
                metadata = PriceHistoryService.get_polling_metadata()
                
                if not metadata['polling_enabled']:
                    logger.debug("Price polling disabled, sleeping...")
                    await asyncio.sleep(60)  # Check again in 1 minute
                    continue
                
                # Update interval from metadata if changed
                self._poll_interval_seconds = metadata['poll_interval_minutes'] * 60
                
                # Check if it's time for an item sync (Wednesday ~3pm UTC)
                await self._check_item_sync(metadata)

                # Perform the poll
                await self._poll_prices()
                
                # Sleep until next poll
                await asyncio.sleep(self._poll_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                # Wait a bit before retrying on error
                await asyncio.sleep(60)
    
    async def _poll_prices(self):
        """
        Fetch current prices and save them to the database
        """
        try:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 🔄 Background Task: Polling fresh prices from OSRS Wiki...")
            logger.info("Polling prices from OSRS Wiki API...")
            
            # Try /5m endpoint first (has volume data)
            try:
                data = fetch_5m_volume_data(use_cache=False)
                data_source = '/5m'
            except Exception as e:
                logger.warning(f"Failed to fetch from /5m endpoint: {e}, falling back to /latest")
                data = fetch_latest_prices(use_cache=False)
                data_source = '/latest'
            
            # Extract price data
            if 'data' in data:
                item_data = data['data']
                # If the API provided a top-level timestamp, we could use it here
                # but save_price_snapshot already handles the logic.
            else:
                logger.error(f"Unexpected data format from {data_source} endpoint")
                return
            
            # Save to database
            saved_count = PriceHistoryService.save_price_snapshot(item_data)
            
            logger.info(f"Poll complete: saved {saved_count} snapshots from {data_source} endpoint")
            
            # Periodically clean up old data (once per day)
            metadata = PriceHistoryService.get_polling_metadata()
            last_poll_time = metadata.get('last_poll_time')
            
            if last_poll_time:
                if isinstance(last_poll_time, str):
                    last_poll_dt = datetime.fromisoformat(last_poll_time)
                else:
                    last_poll_dt = last_poll_time
                
                # Ensure timezone awareness for comparison
                if last_poll_dt.tzinfo is None:
                    last_poll_dt = last_poll_dt.replace(tzinfo=timezone.utc)
                
                hours_since_last = (datetime.now(timezone.utc) - last_poll_dt).total_seconds() / 3600
                
                # Run cleanup if it's been more than 24 hours
                if hours_since_last >= 24:
                    deleted = PriceHistoryService.cleanup_old_data(days_to_keep=30)
                    if deleted > 0:
                        logger.info(f"Cleaned up {deleted} old price records")
            
        except Exception as e:
            logger.error(f"Failed to poll prices: {e}", exc_info=True)

    async def _check_item_sync(self, metadata: dict):
        """
        Check if it's time to sync items from mapping (Wednesday ~3pm UTC)
        """
        now = datetime.now(timezone.utc)
        
        # 2 = Wednesday
        if now.weekday() != 2:
            return
            
        # Target window: 15:00 - 16:00 UTC
        if not (15 <= now.hour < 16):
            return
            
        # Check if we've already synced today
        last_sync = metadata.get('last_item_sync_time')
        if last_sync:
            if isinstance(last_sync, str):
                last_sync_dt = datetime.fromisoformat(last_sync)
            else:
                last_sync_dt = last_sync
                
            if last_sync_dt.date() == now.date():
                return
        
        # It's time!
        logger.info("🕒 Scheduled Item Sync: It's Wednesday afternoon UTC. Checking for new items...")
        print(f"[{now.strftime('%H:%M:%S')}] 🕒 Scheduled Item Sync: Fetching new items from OSRS Wiki...")
        try:
            result = ItemService.sync_items_from_api(force_update=False)
            count = result.get('count', 0)
            logger.info(f"Scheduled Item Sync complete: {count} new items found.")
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ✅ Item Sync complete: Added {count} new items.")
        except Exception as e:
            logger.error(f"Failed to perform scheduled item sync: {e}", exc_info=True)
    
    async def poll_now(self) -> int:
        """
        Trigger an immediate poll (useful for manual refreshes or initial seeding)
        
        Returns:
            Number of snapshots saved
        """
        logger.info("Manual poll triggered")
        await self._poll_prices()
        
        metadata = PriceHistoryService.get_polling_metadata()
        return metadata.get('total_snapshots', 0)
    
    def set_interval(self, minutes: int):
        """Change the polling interval"""
        if minutes < 1:
            raise ValueError("Polling interval must be at least 1 minute")
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE price_polling_metadata
                SET poll_interval_minutes = ?
                WHERE id = 1
            ''', (minutes,))
            conn.commit()
        
        self._poll_interval_seconds = minutes * 60
        logger.info(f"Polling interval changed to {minutes} minutes")


# Global instance
price_polling_service = PricePollingService()
