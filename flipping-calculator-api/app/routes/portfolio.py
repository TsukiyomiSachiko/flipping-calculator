from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
import io
from app.models.schemas import (
    PortfolioBuyRequest, PortfolioAddRequest, PortfolioSellRequest,
    PortfolioCancelRequest, UpdateBuyPriceRequest, FlipResponse, TransactionResponse, PortfolioSummary
)
from app.services.portfolio_service import PortfolioService
from app.services.recovery_service import RecoveryAnalysisService
from app.utils.dependencies import get_account_id

router = APIRouter()

@router.post("/buy")
async def log_buy(request: PortfolioBuyRequest, account_id: int = Depends(get_account_id)):
    """Log a buy transaction"""
    try:
        result = PortfolioService.log_buy(
            account_id,
            request.item_name,
            request.quantity,
            request.price,
            request.intended_quantity,
            request.intended_sell_price,
            request.notes
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_to_flip(request: PortfolioAddRequest, account_id: int = Depends(get_account_id)):
    """Add more quantity to an existing flip"""
    try:
        result = PortfolioService.add_to_flip(
            request.flip_id,
            request.quantity,
            request.price,
            request.notes
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/sell")
async def log_sell(request: PortfolioSellRequest, account_id: int = Depends(get_account_id)):
    """Log a sell transaction"""
    try:
        result = PortfolioService.log_sell(
            request.flip_id,
            request.price,
            request.price_total,
            request.quantity,
            request.notes
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_flip(request: PortfolioCancelRequest, account_id: int = Depends(get_account_id)):
    """Cancel a pending flip"""
    try:
        result = PortfolioService.cancel_flip(
            request.flip_id,
            request.reason
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.delete("/flip/{flip_id}")
async def delete_flip(flip_id: int):
    """
    Permanently delete a flip and all its transactions
    
    WARNING: This action is irreversible. Use for removing test data or mistakes.
    """
    try:
        result = PortfolioService.delete_flip(flip_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/flip/{flip_id}/adjust-intended")
async def adjust_intended_quantity(flip_id: int, account_id: int = Depends(get_account_id)):
    """Adjust intended_quantity to match quantity_total"""
    try:
        result = PortfolioService.adjust_intended_quantity(flip_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.patch("/flip/{flip_id}/buy-price")
async def update_buy_price(flip_id: int, request: UpdateBuyPriceRequest, account_id: int = Depends(get_account_id)):
    """Update the buy price for a pending flip"""
    try:
        result = PortfolioService.update_buy_price(flip_id, request.new_price)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending", response_model=List[FlipResponse])
async def get_pending_flips(account_id: int = Depends(get_account_id)):
    """Get all pending flips for the account"""
    try:
        return PortfolioService.get_pending_flips(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending/projections")
async def get_pending_projections(account_id: int = Depends(get_account_id)):
    """Get pending flips with profit projections"""
    try:
        return PortfolioService.get_pending_with_projections(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/completed", response_model=List[FlipResponse])
async def get_completed_flips(
    limit: int = Query(20, description="Number of flips to return", ge=1, le=100),
    account_id: int = Depends(get_account_id)
):
    """Get completed flips"""
    try:
        return PortfolioService.get_completed_flips(account_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cancelled", response_model=List[FlipResponse])
async def get_cancelled_flips(
    limit: int = Query(20, description="Number of flips to return", ge=1, le=100),
    account_id: int = Depends(get_account_id)
):
    """Get cancelled flips"""
    try:
        return PortfolioService.get_cancelled_flips(account_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mutations", response_model=List[TransactionResponse])
async def get_recent_mutations(
    limit: int = Query(50, description="Number of mutations to return", ge=1, le=200),
    account_id: int = Depends(get_account_id)
):
    """Get the most recent mutations across all flips"""
    try:
        return PortfolioService.get_recent_mutations(account_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flips/{flip_id}")
async def get_flip_details(flip_id: int):
    """Get detailed flip information"""
    try:
        details = PortfolioService.get_flip_details(flip_id)
        if not details:
            raise HTTPException(status_code=404, detail="Flip not found")
        return details
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(account_id: int = Depends(get_account_id)):
    """Get portfolio summary for an account"""
    try:
        return PortfolioService.get_summary(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_portfolio_statistics(account_id: int = Depends(get_account_id)):
    """Get detailed portfolio statistics for an account"""
    try:
        return PortfolioService.get_statistics(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recovery/{flip_id}")
async def get_recovery_analysis(flip_id: int):
    """
    Analyse profit recovery probability for a pending flip.

    Uses 6h price history to determine trend direction, volatility,
    historical recovery patterns, and provides a hold/sell recommendation.
    """
    try:
        flip = PortfolioService.get_flip_details(flip_id)
        if not flip:
            raise HTTPException(status_code=404, detail="Flip not found")

        flip_data = flip.get('flip', flip)
        if flip_data.get('status') not in ['pending', 'partially_completed']:
            raise HTTPException(status_code=400, detail=f"Recovery analysis is only available for pending or partially completed flips (current status: {flip_data.get('status')})")

        analysis = RecoveryAnalysisService.analyse_recovery(
            item_id=flip_data['item_id'],
            buy_price=flip_data['buy_price'],
        )

        if not analysis:
            raise HTTPException(status_code=404, detail="Insufficient price history for analysis")

        analysis['flip_id'] = flip_id
        analysis['item_name'] = flip_data['item_name']
        analysis['quantity_remaining'] = flip_data['quantity_remaining']

        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_portfolio(account_id: int = Depends(get_account_id)):
    """Export portfolio to CSV"""
    try:
        csv_content = PortfolioService.export_csv(account_id)
        
        # Create stream
        stream = io.StringIO(csv_content)
        
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=portfolio_export_account_{account_id}.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_portfolio(file: UploadFile = File(...), account_id: int = Depends(get_account_id)):
    """Import portfolio from CSV"""
    try:
        content = await file.read()
        # Decode bytes to string
        csv_text = content.decode('utf-8')
        result = PortfolioService.import_csv(account_id, csv_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()