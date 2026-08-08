"""Event models — PRD Section 35 (market_events + news_events)."""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MarketEvent(Base):
    """Canonical market/price event — PRD Section 23."""
    __tablename__ = "market_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # "simulation" or provider name
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PRICE_MOVEMENT, etc.
    symbol: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class NewsEvent(Base):
    """News event with AI analysis — PRD Section 23."""
    __tablename__ = "news_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=True)
    ai_analysis: Mapped[dict] = mapped_column(JSON, nullable=True)  # LLM structured output
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
