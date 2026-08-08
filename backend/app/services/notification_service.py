"""
Notification Service — PRD Sections 17, 33, 50.
Handles outbound notifications across channels, retries, and escalation.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional

from app.core.logging import get_logger
from app.models.notification import Notification, NotificationStatus
from app.models.alert import Alert, AlertStatus
from app.models.preference import NotificationPreference

logger = get_logger("notification_service")


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def dispatch_alert_notifications(self, alert: Alert):
        """
        Determine channels based on severity and preferences,
        then queue notifications.
        """
        if alert.status in [AlertStatus.NORMAL, AlertStatus.WATCHING]:
            return  # No notifications for info/watching levels
            
        prefs = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == alert.user_id
        ).first()
        
        if not prefs:
            logger.warning(f"No preferences found for user {alert.user_id}, using default email")
            channels = ["email"]
        else:
            if alert.severity_level == AlertStatus.CRITICAL:
                channels = prefs.critical_channel.split(",")
            elif alert.severity_level == AlertStatus.HIGH:
                channels = prefs.high_channel.split(",")
            else:
                channels = prefs.warning_channel.split(",")
                
        for ch in channels:
            ch = ch.strip()
            if not ch: continue
            
            notif = Notification(
                alert_id=alert.alert_id,
                channel=ch,
                status=NotificationStatus.PENDING
            )
            self.db.add(notif)
            logger.info(f"Queued {ch} notification for alert {alert.alert_id}")
            
        self.db.commit()
        
        # Trigger actual sending (in MVP this could just call the sender directly)
        # return self.process_pending_notifications()

    def update_notification_status(self, notification_id: int, status: NotificationStatus, message_id: str = None, error: str = None):
        """Update the status of a notification after sending via Caspian."""
        notif = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return
            
        notif.status = status
        if message_id:
            notif.provider_message_id = message_id
            
        if status == NotificationStatus.SENT:
            notif.sent_at = datetime.now(timezone.utc)
        elif status == NotificationStatus.FAILED:
            notif.failure_reason = error
            
        self.db.commit()

    def get_notifications_for_alert(self, alert_id: str) -> List[Notification]:
        return self.db.query(Notification).filter(Notification.alert_id == alert_id).all()
