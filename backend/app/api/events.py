"""
Event API endpoints — PRD Section 36.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.event_service import EventService
from app.schemas.event import MarketEventResponse, NewsEventResponse

router = APIRouter()


@router.get("/events/market", response_model=List[MarketEventResponse])
def get_recent_market_events(limit: int = 50, db: Session = Depends(get_db)):
    """Recent market events."""
    service = EventService(db)
    return service.get_recent_market_events(limit=limit)


@router.get("/events/news", response_model=List[NewsEventResponse])
def get_recent_news_events(limit: int = 20, db: Session = Depends(get_db)):
    """Recent news events."""
    service = EventService(db)
    return service.get_recent_news_events(limit=limit)
