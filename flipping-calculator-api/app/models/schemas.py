from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Item models
class ItemBase(BaseModel):
    id: int
    name: str
    examine: Optional[str] = None
    members: bool
    ge_limit: int
    icon: Optional[str] = None

class ItemWithPrices(ItemBase):
    buy_price: Optional[int] = None
    sell_price: Optional[int] = None
    profit: Optional[int] = None
    roi: Optional[float] = None
    volume: Optional[int] = None
    volume_indicator: Optional[str] = None
    profit_at_limit: Optional[int] = None

# Flip search parameters
class FlipSearchParams(BaseModel):
    min_profit: Optional[int] = 0
    min_roi: Optional[float] = 0
    max_roi: Optional[float] = 25.0
    min_limit_profit: Optional[int] = 0
    min_volume: Optional[int] = 0
    high_volume_only: bool = False
    cash: Optional[int] = None
    members_only: bool = False
    f2p_only: bool = False
    sort_by: str = "profit"  # profit, roi, limit, volume
    limit: int = 20

# Portfolio models
class PortfolioBuyRequest(BaseModel):
    item_name: str
    quantity: int
    price: int
    intended_quantity: Optional[int] = None
    intended_sell_price: Optional[int] = None
    notes: Optional[str] = None

class PortfolioAddRequest(BaseModel):
    flip_id: int
    quantity: int
    price: int
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PortfolioSellRequest(BaseModel):
    flip_id: int
    price: Optional[int] = None
    price_total: Optional[int] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None

class PortfolioCancelRequest(BaseModel):
    flip_id: int
    reason: Optional[str] = None

class UpdateBuyPriceRequest(BaseModel):
    new_price: int

class FlipResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity_total: int
    quantity_remaining: int
    buy_price: int
    sell_price: Optional[int] = None
    buy_time: datetime
    sell_time: Optional[datetime] = None
    profit: Optional[int] = None
    roi: Optional[float] = None
    status: str
    cancel_reason: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TransactionResponse(BaseModel):
    id: int
    flip_id: int
    transaction_type: str
    mutation_type: Optional[str] = None
    item_name: Optional[str] = None
    item_id: Optional[int] = None
    quantity: Optional[int] = None
    price: Optional[int] = None
    timestamp: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PortfolioSummary(BaseModel):
    total_flips: int
    winning_flips: int
    losing_flips: int
    total_profit: int
    pending_profit: int
    total_profit_all: int
    avg_roi: float
    roi_in_progress: float
    best_flip: int
    worst_flip: int
    total_invested: int
    pending_flips: int
    pending_capital: int
    cancelled_flips: int