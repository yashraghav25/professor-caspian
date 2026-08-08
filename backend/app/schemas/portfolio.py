"""Pydantic schemas for Portfolio API — PRD Section 36."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Request Schemas ──

class PortfolioCreate(BaseModel):
    name: str = "Default Portfolio"
    base_currency: str = "USD"


class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    average_price: float
    current_price: Optional[float] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    average_price: Optional[float] = None
    current_price: Optional[float] = None


# ── Response Schemas ──

class HoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    average_price: float
    current_price: Optional[float]
    position_value: float
    weight: float  # portfolio weight as percentage
    unrealized_pnl: float
    change_percent: float

    model_config = {"from_attributes": True}


class PortfolioResponse(BaseModel):
    id: int
    name: str
    base_currency: str
    total_value: float
    invested_value: float
    cash_value: float
    total_pnl: float
    total_pnl_percent: float
    holdings: list[HoldingResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
