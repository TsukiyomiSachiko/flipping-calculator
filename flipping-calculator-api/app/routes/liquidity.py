"""
Liquidity analysis routes
"""

from fastapi import APIRouter, Query
from app.services.liquidity_service import LiquidityService

router = APIRouter()


@router.get("/items/{item_id}/liquidity")
async def get_liquidity_insights(
    item_id: int,
    hours: int = Query(default=168, ge=24, le=720, description="Hours of history to analyze (1-30 days)")
):
    """
    Get liquidity timing insights for an item.
    
    Analyzes volume patterns to help users understand:
    - When the item typically fills (hourly patterns)
    - Whether liquidity is consistent or comes in waves
    - Estimated time between fill opportunities
    - Best trading hours
    
    Args:
        item_id: Item ID to analyze
        hours: Hours of history to analyze (default: 168 = 7 days)
    
    Returns:
        Liquidity insights including pattern classification, best hours, and fill estimates
    """
    return LiquidityService.get_liquidity_insights(item_id, hours)
