from fastapi import APIRouter, HTTPException, Query
from app.services.trajectory_service import TrajectoryService
from app.utils.database import get_db, execute_query, executemany_query

router = APIRouter()


@router.get("/items/{item_id}/trajectory")
async def get_trajectory(
    item_id: int,
    timestep: str = Query('1h', description="Time interval: 5m, 1h, or 6h", pattern="^(5m|1h|6h)$")
):
    """
    Get market trajectory analysis for an item.

    Returns smoothed price history, forward projection with confidence bands,
    trend classification, and summary statistics.

    - **item_id**: The OSRS item ID
    - **timestep**: Time interval ('5m', '1h', or '6h')
    """
    # Verify item exists
    with get_db() as session:
        _res = execute_query(session, 'SELECT id, name FROM items WHERE id = ?', (item_id,))
        item = _res.mappings().fetchone()

        if not item:
            raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")

    result = TrajectoryService.compute_trajectory(item_id, timestep)

    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Not enough price data to compute trajectory (need at least 6 data points)"
        )

    return {
        "item_id": item_id,
        "item_name": item['name'],
        "timestep": timestep,
        **result,
    }
