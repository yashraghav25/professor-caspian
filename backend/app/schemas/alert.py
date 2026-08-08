"""Pydantic schemas for Alerts — PRD Section 36."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    alert_id: str
    event_id: str
    severity_score: float
    severity_level: str
    title: str
    reason: Optional[str]
    status: str
    acknowledged_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    notifications: list["NotificationBrief"] = []

    model_config = {"from_attributes": True}


class NotificationBrief(BaseModel):
    id: int
    channel: str
    status: str
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AcknowledgeRequest(BaseModel):
    """User acknowledges an alert."""
    message: Optional[str] = "Acknowledged"
