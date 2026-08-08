"""
Event Service — PRD Sections 24, 50.
Handles ingestion, validation, persistence, and deduplication of events.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import uuid

from app.core.logging import get_logger
from app.models.event import MarketEvent, NewsEvent
from app.schemas.event import EventBase, MarketEventResponse, NewsEventResponse

logger = get_logger("event_service")


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_event(self, event: EventBase) -> Optional[str]:
        """
        Ingest an event (market or news).
        Persists and deduplicates based on event_id.
        Returns the internal database ID of the created event, or None if duplicate.
        """
        logger.info(f"Ingesting event {event.event_id} of type {event.event_type}")

        if event.event_type == "NEWS":
            return self._ingest_news_event(event)
        else:
            return self._ingest_market_event(event)

    def _ingest_market_event(self, event: EventBase) -> Optional[int]:
        """Persist a market event if it doesn't already exist."""
        # Deduplication check
        existing = self.db.query(MarketEvent).filter(MarketEvent.event_id == event.event_id).first()
        if existing:
            logger.info(f"MarketEvent {event.event_id} already exists. Skipping.")
            return None

        new_event = MarketEvent(
            event_id=event.event_id,
            source=event.source,
            event_type=event.event_type,
            symbol=event.symbol,
            payload=event.payload,
            occurred_at=event.occurred_at
        )
        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)
        return new_event.id

    def _ingest_news_event(self, event: EventBase) -> Optional[int]:
        """Persist a news event if it doesn't already exist."""
        # Deduplication check
        existing = self.db.query(NewsEvent).filter(NewsEvent.event_id == event.event_id).first()
        if existing:
            logger.info(f"NewsEvent {event.event_id} already exists. Skipping.")
            return None

        payload = event.payload
        new_event = NewsEvent(
            event_id=event.event_id,
            headline=payload.get("headline", "No Headline"),
            summary=payload.get("summary"),
            source=payload.get("source_name", event.source),
            url=payload.get("url"),
            ai_analysis=payload.get("ai_analysis"),
        )
        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)
        return new_event.id

    def get_recent_market_events(self, limit: int = 50) -> List[MarketEventResponse]:
        """Fetch recent market events ordered by occurrence time."""
        events = self.db.query(MarketEvent).order_by(MarketEvent.occurred_at.desc()).limit(limit).all()
        return [MarketEventResponse.model_validate(e) for e in events]

    def get_recent_news_events(self, limit: int = 20) -> List[NewsEventResponse]:
        """Fetch recent news events ordered by creation time."""
        events = self.db.query(NewsEvent).order_by(NewsEvent.created_at.desc()).limit(limit).all()
        return [NewsEventResponse.model_validate(e) for e in events]
        
    def generate_event_id(self, prefix: str = "evt") -> str:
        """Helper to generate a unique event ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
