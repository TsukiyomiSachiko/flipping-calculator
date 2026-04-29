from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.utils.api_client import fetch_price_timeseries
from app.utils.database import get_db, execute_query, executemany_query

router = APIRouter()

@router.get("/items/{item_id}/price-history")
async def get_price_history(
    item_id: int,
    timestep: str = Query('5m', description="Time interval: 5m, 1h, or 6h", pattern="^(5m|1h|6h)$")
):
    """
    Get price history for a specific item
    
    Returns timeseries data with timestamps and price information.
    
    - **item_id**: The OSRS item ID
    - **timestep**: Time interval ('5m', '1h', or '6h')
    """
    try:
        # Verify item exists in database
        with get_db() as session:
            _res = execute_query(session, 'SELECT id, name FROM items WHERE id = ?', (item_id,))
            item = _res.mappings().fetchone()
            
            if not item:
                raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
        
        # Fetch timeseries data from OSRS Wiki
        data = fetch_price_timeseries(item_id, timestep)
        
        # Add item info to response
        return {
            "item_id": item_id,
            "item_name": item['name'],
            "timestep": timestep,
            "data": data.get('data', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
