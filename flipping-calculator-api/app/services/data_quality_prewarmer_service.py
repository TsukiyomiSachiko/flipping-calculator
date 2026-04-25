"""
Background Data Quality Pre-Warmer Service

Periodically pre-calculates and caches historical volatility and stability
for all items to ensure instant response times for API requests.
Runs as a background task in FastAPI using asyncio.

Features:
- Pre-warms the cache on application startup
- Runs every hour to keep the cache fresh
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from app.services.data_quality_service import DataQualityService

logger = logging.getLogger(__name__)


class DataQualityPrewarmerService:
    """Background service that pre-calculates data quality metrics"""
    
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._should_run = True
        self._poll_interval_seconds = 3600  # 1 hour default
    
    async def start(self):
        """Start the background pre-warmer task"""
        if self._task is not None and not self._task.done():
            logger.warning("Data quality prewarmer service already running")
            return
        
        logger.info("Starting data quality prewarmer service...")
        self._should_run = True
        self._task = asyncio.create_task(self._prewarming_loop())
    
    async def stop(self):
        """Stop the background pre-warmer task"""
        logger.info("Stopping data quality prewarmer service...")
        self._should_run = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Data quality prewarmer service stopped")
    
    async def _prewarming_loop(self):
        """Main pre-warming loop that runs continuously"""
        # Wait a bit before first poll to allow app to fully start
        # and price_polling_service to initialize
        await asyncio.sleep(5)
        
        while self._should_run:
            try:
                logger.info("Running scheduled DataQualityService cache prewarm...")
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 🚀 Background Task: Pre-warming Data Quality cache...")
                
                # Run the synchronous prewarm in an executor to avoid blocking the event loop
                await asyncio.to_thread(DataQualityService.prewarm_cache)
                
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ✅ Data Quality cache pre-warmed successfully!")
                
                # Sleep until next prewarm
                await asyncio.sleep(self._poll_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Pre-warming loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in pre-warming loop: {e}", exc_info=True)
                # Wait a bit before retrying on error
                await asyncio.sleep(300)  # Retry in 5 minutes

    async def prewarm_now(self):
        """Trigger an immediate prewarm"""
        logger.info("Manual data quality prewarm triggered")
        await asyncio.to_thread(DataQualityService.prewarm_cache)

# Global instance
data_quality_prewarmer_service = DataQualityPrewarmerService()
