"""Pydantic schemas for Notifications — PRD Section 36."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    alert_id: str
    channel: str
    status: str
    provider_message_id: Optional[str]
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    failure_reason: Optional[str]
    retry_count: int

    model_config = {"from_attributes": True}
