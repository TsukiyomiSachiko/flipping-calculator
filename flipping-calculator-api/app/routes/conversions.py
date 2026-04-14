from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict
from app.services.conversion_service import ConversionService

router = APIRouter(tags=["Conversions"])

@router.get("", response_model=List[Dict])
async def get_conversions():
    """Get all item conversions with live profit data."""
    try:
        return ConversionService.get_conversions_with_prices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_conversions(background_tasks: BackgroundTasks):
    """Trigger a sync of conversions from the OSRS Wiki."""
    # We can run it in background or directly. Since it's a few dozen pages, direct is okay for now.
    try:
        result = ConversionService.sync_conversions_from_wiki()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
