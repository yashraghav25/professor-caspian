"""Pydantic schemas for Events — PRD Section 23."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class EventBase(BaseModel):
    """Canonical event schema — all events (real or simulated) use this."""
    event_id: str
    event_type: str  # PRICE_MOVEMENT, NEWS, etc.
    source: str  # "simulation", "yahoo", "finnhub", etc.
    symbol: Optional[str] = None
    payload: dict
    occurred_at: datetime


class PriceEventPayload(BaseModel):
    """Payload for PRICE_MOVEMENT events."""
    price: float
    previous_price: float
    change_percent: float
    volume_ratio: Optional[float] = 1.0


class NewsEventPayload(BaseModel):
    """Payload for NEWS events."""
    headline: str
    summary: Optional[str] = None
    source_name: str = "Demo News Feed"
    url: Optional[str] = None


class CustomEventInject(BaseModel):
    """Schema for injecting custom events via the simulation API."""
    type: str  # "PRICE_MOVEMENT" or "NEWS"
    symbol: Optional[str] = None
    change_percent: Optional[float] = None
    headline: Optional[str] = None
    summary: Optional[str] = None


class MarketEventResponse(BaseModel):
    id: int
    event_id: str
    source: str
    event_type: str
    symbol: Optional[str]
    payload: dict
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsEventResponse(BaseModel):
    id: int
    event_id: str
    headline: str
    summary: Optional[str]
    source: str
    ai_analysis: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsAnalysisSchema(BaseModel):
    """LLM structured output for news analysis — PRD Section 28, 72."""
    entities: list[str]
    sectors: list[str]
    sentiment: Literal["positive", "neutral", "negative"]
    impact: Literal["low", "medium", "high"]
    confidence: float
    reason: str
