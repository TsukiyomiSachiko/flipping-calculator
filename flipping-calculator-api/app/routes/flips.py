from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict
from app.models.schemas import ItemWithPrices, FlipSearchParams
from app.services.flip_service import FlipService
from app.services.trending_service import TrendingService
from app.utils.dependencies import get_account_id

router = APIRouter()


@router.get("/trending")
async def get_trending_flips(
    cash: Optional[int] = Query(None, description="Optional cash override"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=50),
    account_id: int = Depends(get_account_id)
):
    """Get top trending items ranked by price momentum."""
    try:
        results = TrendingService.get_trending_flips(account_id, cash=cash, limit=limit)
        return {
            "count": len(results),
            "flips": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_profitable_flips(
    min_profit: Optional[int] = Query(0),
    min_roi: Optional[float] = Query(0),
    max_roi: Optional[float] = Query(25.0),
    min_limit_profit: Optional[int] = Query(0),
    min_volume: Optional[int] = Query(0),
    high_volume_only: bool = Query(False),
    cash: Optional[int] = Query(None),
    members_only: bool = Query(False),
    f2p_only: bool = Query(False),
    sort_by: str = Query("profit"),
    limit: int = Query(20, ge=1, le=100),
    enable_quality_filter: bool = Query(False),
    require_grindable: bool = Query(False),
    account_id: int = Depends(get_account_id)
):
    """Find profitable flips based on search criteria"""
    try:
        params = {
            "min_profit": min_profit, "min_roi": min_roi, "max_roi": max_roi,
            "min_limit_profit": min_limit_profit, "min_volume": min_volume,
            "high_volume_only": high_volume_only, "cash": cash,
            "members_only": members_only, "f2p_only": f2p_only,
            "sort_by": sort_by, "limit": limit,
            "enable_quality_filter": enable_quality_filter,
            "require_grindable": require_grindable,
        }
        results = FlipService.get_profitable_flips(account_id, params)
        return {"count": len(results), "filters": params, "flips": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_profitable_flips_post(params: FlipSearchParams, account_id: int = Depends(get_account_id)):
    """Find profitable flips using POST"""
    try:
        results = FlipService.get_profitable_flips(account_id, params.dict())
        return {"count": len(results), "filters": params.dict(), "flips": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_flip_stats():
    """Get statistics about available flips"""
    try:
        stats = FlipService.get_flip_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))