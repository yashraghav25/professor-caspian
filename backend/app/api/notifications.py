"""
Notification API endpoints — PRD Section 36.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationResponse

router = APIRouter()

@router.get("/alerts/{alert_id}/notifications", response_model=List[NotificationResponse])
def get_notifications(alert_id: str, db: Session = Depends(get_db)):
    """Get all notifications for an alert."""
    service = NotificationService(db)
    notifications = service.get_notifications_for_alert(alert_id)
    return notifications
