"""Notification preferences model — PRD Section 35."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    warning_channel: Mapped[str] = mapped_column(String(50), nullable=False, default="email")
    high_channel: Mapped[str] = mapped_column(String(50), nullable=False, default="email,telegram")
    critical_channel: Mapped[str] = mapped_column(String(50), nullable=False, default="email,telegram")
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    escalation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User", back_populates="preferences")
