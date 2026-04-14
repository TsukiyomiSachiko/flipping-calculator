from fastapi import APIRouter, HTTPException, Query, Depends, Header
from typing import List, Optional
from app.models.schemas import ItemBase, ItemWithPrices
from app.services.item_service import ItemService
from app.services.settings_service import SettingsService
from app.utils.api_client import clear_all_caches
from app.utils.dependencies import get_account_id

router = APIRouter()

@router.post("/sync")
async def sync_items():
    """Sync items from OSRS Wiki API to database (first-time setup)"""
    try:
        result = ItemService.sync_items_from_api()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ItemBase])
async def get_all_items(
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get all items from database"""
    try:
        items = ItemService.get_all_items()
        
        if offset:
            items = items[offset:]
        if limit:
            items = items[:limit]
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_items(
    q: str = Query(..., description="Search query"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search items by name"""
    try:
        items = ItemService.search_items(q)
        return items[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_id}")
async def get_item(item_id: int):
    """Get single item by ID"""
    try:
        item = ItemService.get_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_id}/prices")
async def get_item_with_prices(
    item_id: int,
    cash: Optional[int] = Query(None, description="Available cash for max qty calculation"),
    x_account_id: Optional[str] = Header(None)
):
    """Get single item enriched with live price data, profit calculations, and volume"""
    try:
        # Auto-fetch cash if not provided but account is
        if cash is None and x_account_id:
            try:
                settings = SettingsService.get_settings(int(x_account_id))
                cash = settings.get('available_cash')
            except:
                pass

        result = ItemService.get_item_with_prices(item_id, cash)
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-cache")
async def clear_cache():
    """Clear all API caches"""
    try:
        clear_all_caches()
        return {"message": "All caches cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))