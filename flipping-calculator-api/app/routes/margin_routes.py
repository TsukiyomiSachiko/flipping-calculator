"""
Margin Tracking Routes

API endpoints for analyzing profit margins over time
"""

from fastapi import APIRouter, HTTPException, Query
from app.services.margin_tracking_service import MarginTrackingService

router = APIRouter(prefix="/margins", tags=["margins"])


@router.get("/item/{item_id}")
async def get_item_margin_analysis(
    item_id: int,
    hours: int = Query(168, ge=24, le=720, description="Hours of history to analyze (24-720, default 168 = 7 days)"),
    interval: str = Query('1h', pattern='^(1h|6h|1d)$', description="Aggregation interval")
):
    """
    Analyze profit margins over time for a specific item
    
    Returns:
    - Current, average, min, max margins
    - Peak trading times (best hours/days for margins)
    - Trend analysis (increasing/decreasing/stable)
    - Time-series data of margins
    
    **Use cases:**
    - Identify best times to flip an item
    - See if margins are improving or declining
    - Find patterns in margin fluctuations
    """
    try:
        print(f"DEBUG: Starting margin analysis for item_id={item_id}, hours={hours}, interval={interval}")
        analysis = MarginTrackingService.analyze_item_margins(
            item_id=item_id,
            hours=hours,
            interval=interval
        )
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient price history for item {item_id}. "
                       "Need at least 10 data points with both buy and sell prices."
            )
        
        print(f"DEBUG: Successfully completed margin analysis for item {item_id}")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in margin analysis: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))