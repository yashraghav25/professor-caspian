"""
Alert Service — PRD Sections 16, 18, 19, 50.
Manages alert state machine, deduplication, and transitions.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Optional

from app.core.logging import get_logger
from app.models.alert import Alert, AlertStatus
from app.models.notification import Notification, NotificationStatus
from app.schemas.alert import AlertResponse
from app.core.config import settings

logger = get_logger("alert_service")


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def generate_alert_id(self) -> str:
        return f"alt_{uuid.uuid4().hex[:8]}"

    def process_alert_transition(
        self, 
        user_id: int, 
        portfolio_id: int, 
        event_id: str, 
        severity_score: float, 
        severity_level: AlertStatus,
        title: str,
        reason: str
    ) -> Optional[Alert]:
        """
        Process the state transition for an alert.
        Handles deduplication and cooldowns.
        """
        # We group alerts by user + related event logic.
        # For simplicity, if we have an active alert for the same user in the last N seconds, 
        # we update it instead of creating a new one (suppression/cooldown).
        
        cooldown_threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.alert_cooldown_seconds)
        
        recent_alert = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.updated_at >= cooldown_threshold,
            Alert.status.in_([
                AlertStatus.WARNING, 
                AlertStatus.HIGH, 
                AlertStatus.CRITICAL
            ])
        ).order_by(Alert.updated_at.desc()).first()

        # If we have a recent active alert, and this new severity isn't higher, suppress it
        if recent_alert and not self._is_escalation(recent_alert.severity_level, severity_level):
            logger.info(f"Suppressing alert {event_id}. Cooldown active. Existing: {recent_alert.severity_level}, New: {severity_level}")
            return None
            
        # Create new or escalate
        alert = Alert(
            alert_id=self.generate_alert_id(),
            user_id=user_id,
            portfolio_id=portfolio_id,
            event_id=event_id,
            severity_score=severity_score,
            severity_level=severity_level,
            title=title,
            reason=reason,
            status=severity_level
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Created new alert {alert.alert_id} with severity {severity_level}")
        return alert

    def _is_escalation(self, old_level: AlertStatus, new_level: AlertStatus) -> bool:
        """Returns True if the new level is strictly more severe than the old level."""
        levels = {
            AlertStatus.NORMAL: 0,
            AlertStatus.WATCHING: 1,
            AlertStatus.WARNING: 2,
            AlertStatus.HIGH: 3,
            AlertStatus.CRITICAL: 4,
            AlertStatus.ACKNOWLEDGED: 5,
            AlertStatus.RESOLVED: 6
        }
        
        # If acknowledged or resolved, a new CRITICAL/HIGH event might re-trigger, 
        # but usually we want to start fresh.
        if old_level in [AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED]:
            return True
            
        return levels.get(new_level, 0) > levels.get(old_level, 0)

    def acknowledge_alert(self, user_id: int, alert_id: str) -> Optional[Alert]:
        """Acknowledge an alert (user replied via Caspian)."""
        alert = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.alert_id == alert_id
        ).first()
        
        if not alert:
            return None
            
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        # An acknowledgement is an incident-level action. Reflect it on every
        # delivery record so the dashboard can show a complete audit trail.
        self.db.query(Notification).filter(
            Notification.alert_id == alert_id,
            Notification.status.in_([NotificationStatus.PENDING, NotificationStatus.SENT, NotificationStatus.DELIVERED]),
        ).update(
            {
                Notification.status: NotificationStatus.ACKNOWLEDGED,
                Notification.acknowledged_at: alert.acknowledged_at,
            },
            synchronize_session=False,
        )
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
        return alert

    def get_active_alerts(self, user_id: int, limit: int = 10) -> List[AlertResponse]:
        alerts = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.status.in_([AlertStatus.WARNING, AlertStatus.HIGH, AlertStatus.CRITICAL, AlertStatus.ACKNOWLEDGED])
        ).order_by(Alert.updated_at.desc()).limit(limit).all()
        
        return [AlertResponse.model_validate(a) for a in alerts]

    def get_latest_active_alert(self, user_id: int) -> Optional[Alert]:
        """Return the most recent active alert ORM object (for attaching AI summary)."""
        return (
            self.db.query(Alert)
            .filter(
                Alert.user_id == user_id,
                Alert.status.in_(
                    [AlertStatus.WARNING, AlertStatus.HIGH, AlertStatus.CRITICAL]
                ),
            )
            .order_by(Alert.updated_at.desc())
            .first()
        )
        
    def get_alert(self, user_id: int, alert_id: str) -> Optional[AlertResponse]:
        alert = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.alert_id == alert_id
        ).first()
        
        return AlertResponse.model_validate(alert) if alert else None
