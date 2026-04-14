"""
Price History Routes

API endpoints for:
- Querying local price history
- Managing the polling service
- Viewing database statistics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.price_history_service import PriceHistoryService
from app.services.price_polling_service import price_polling_service

router = APIRouter(prefix="/price-history", tags=["price-history"])


@router.get("/item/{item_id}")
async def get_item_price_history(
    item_id: int,
    hours: int = Query(24, ge=1, le=720, description="Hours of history to retrieve (1-720)"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Max records to return")
):
    """
    Get raw price history for a specific item from local database
    
    Returns individual price snapshots (not aggregated)
    """
    try:
        history = PriceHistoryService.get_item_history(item_id, hours=hours, limit=limit)
        
        return {
            'item_id': item_id,
            'hours': hours,
            'count': len(history),
            'data': history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeseries/{item_id}")
async def get_item_timeseries(
    item_id: int,
    timestep: str = Query('5m', pattern='^(5m|1h|6h)$', description="Aggregation interval"),
    hours: int = Query(24, ge=1, le=720, description="Hours of history to include")
):
    """
    Get aggregated timeseries data for a specific item
    
    Mimics the structure of OSRS Wiki's /timeseries endpoint but uses local data.
    This endpoint can replace calls to the Wiki's timeseries API.
    """
    try:
        timeseries = PriceHistoryService.get_timeseries(item_id, timestep=timestep, hours=hours)
        
        if not timeseries['data']:
            raise HTTPException(
                status_code=404, 
                detail=f"No local price history available for item {item_id}. "
                       "The polling service may need time to collect data."
            )
        
        return {
            'item_id': item_id,
            'timestep': timestep,
            'hours': hours,
            'count': len(timeseries['data']),
            'data': timeseries['data']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_database_stats():
    """
    Get statistics about the local price history database
    
    Returns information about:
    - Total records stored
    - Number of unique items tracked
    - Date range of available data
    - Current polling status
    """
    try:
        db_stats = PriceHistoryService.get_database_stats()
        polling_metadata = PriceHistoryService.get_polling_metadata()
        
        return {
            'database': db_stats,
            'polling': polling_metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poll/trigger")
async def trigger_manual_poll():
    """
    Trigger an immediate price poll (useful for initial setup or manual refresh)
    
    This will fetch current prices from OSRS Wiki API and save them to the database.
    """
    try:
        await price_polling_service.poll_now()
        
        metadata = PriceHistoryService.get_polling_metadata()
        
        return {
            'success': True,
            'message': 'Manual poll completed',
            'total_snapshots': metadata['total_snapshots']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poll/enable")
async def enable_polling(enabled: bool = True):
    """
    Enable or disable automatic price polling
    
    When enabled, the service will poll prices every N minutes (configurable).
    When disabled, no automatic polling occurs (manual polls still work).
    """
    try:
        PriceHistoryService.set_polling_enabled(enabled)
        
        return {
            'success': True,
            'message': f"Polling {'enabled' if enabled else 'disabled'}",
            'polling_enabled': enabled
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_data(days_to_keep: int = Query(30, ge=1, le=365)):
    """
    Clean up old price history data
    
    Removes price snapshots older than the specified number of days.
    Default is 30 days. Maximum retention is 365 days.
    """
    try:
        deleted = PriceHistoryService.cleanup_old_data(days_to_keep=days_to_keep)
        
        return {
            'success': True,
            'message': f'Cleaned up {deleted} old records',
            'deleted_count': deleted,
            'days_retained': days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
