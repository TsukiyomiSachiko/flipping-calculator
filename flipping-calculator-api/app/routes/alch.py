from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from app.services.alch_service import AlchService

router = APIRouter(prefix="/alch", tags=["High Alchemy"])

@router.get("/profitable", response_model=List[Dict])
async def get_profitable_alchs(
    limit: int = Query(500, ge=1, le=2000, description="Max items to return"),
    min_volume: int = Query(1, ge=0, description="Minimum hourly trading volume (defaults to 1 to hide items with 0 volume)")
):
    """Get all items that yield a profit when High-Alched, sorted by profit at GE limit."""
    try:
        return AlchService.get_profitable_alchs(limit=limit, min_volume=min_volume)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
