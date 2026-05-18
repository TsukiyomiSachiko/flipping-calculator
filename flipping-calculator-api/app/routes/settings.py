"""
User settings routes
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.settings_service import SettingsService
from app.utils.dependencies import get_account_id

router = APIRouter()


class SetCashRequest(BaseModel):
    amount: int


class SetCashflowSettingsRequest(BaseModel):
    profit_take_pct: float
    loss_refill_pct: float


@router.get("/settings")
async def get_settings(account_id: int = Depends(get_account_id)):
    """Get user settings including available cash"""
    return SettingsService.get_settings(account_id)


@router.post("/settings/cash")
async def set_available_cash(request: SetCashRequest, account_id: int = Depends(get_account_id)):
    """
    Set available cash for flipping
    """
    return SettingsService.set_available_cash(account_id, request.amount)

@router.post("/settings/cashflow")
async def set_cashflow_settings(request: SetCashflowSettingsRequest, account_id: int = Depends(get_account_id)):
    """
    Set cashflow settings (profit take % and loss refill %)
    """
    return SettingsService.set_cashflow_settings(account_id, request.profit_take_pct, request.loss_refill_pct)
