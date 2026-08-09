"""Escalate material incidents that have not been acknowledged via Caspian."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.caspian.client import get_caspian
from app.caspian.message_builder import build_escalation_email
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.alert import Alert, AlertStatus
from app.models.notification import Notification, NotificationStatus
from app.services.notification_service import NotificationService

logger = get_logger("escalation_worker")

ESCALATION_CHANNEL = "escalation_email"
_worker_active = False
_worker_task = None


async def start_escalation_worker():
    global _worker_active, _worker_task
    if _worker_active:
        return
    _worker_active = True
    _worker_task = asyncio.create_task(_escalation_loop())
    logger.info("No-ack escalation worker started (delay=%ss).", settings.escalation_delay_seconds)


async def stop_escalation_worker():
    global _worker_active, _worker_task
    _worker_active = False
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
    _worker_task = None


async def _escalation_loop():
    # Allow normal alert delivery to finish before the first scan.
    await asyncio.sleep(10)
    while _worker_active:
        try:
            await run_escalation_scan()
        except Exception as exc:
            logger.error("No-ack escalation scan failed: %s", exc)
        await asyncio.sleep(10)


async def run_escalation_scan() -> int:
    """Escalate every overdue HIGH/CRITICAL alert once; returns number escalated."""
    db = SessionLocal()
    escalated = 0
    try:
        candidates = (
            db.query(Alert)
            .filter(
                Alert.status.in_([AlertStatus.HIGH, AlertStatus.CRITICAL]),
            )
            .all()
        )
        now = datetime.now(timezone.utc)
        for alert in candidates:
            created_at = alert.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_seconds = int((now - created_at).total_seconds())
            if age_seconds < settings.escalation_delay_seconds:
                continue

            already_escalated = (
                db.query(Notification.id)
                .filter(
                    Notification.alert_id == alert.alert_id,
                    Notification.channel == ESCALATION_CHANNEL,
                )
                .first()
            )
            if already_escalated:
                continue

            notification = Notification(
                alert_id=alert.alert_id,
                channel=ESCALATION_CHANNEL,
                status=NotificationStatus.PENDING,
            )
            db.add(notification)
            db.flush()

            try:
                subject, plain, html = build_escalation_email(alert, age_seconds)
                result = await get_caspian().send_email(
                    settings.escalation_recipient, subject, plain, html
                )
                NotificationService(db).update_notification_status(
                    notification.id,
                    NotificationStatus.SENT,
                    message_id=result.get("id") or result.get("status"),
                )
                escalated += 1
                logger.warning("Escalated unacknowledged alert %s via Caspian email.", alert.alert_id)
            except Exception as exc:
                NotificationService(db).update_notification_status(
                    notification.id, NotificationStatus.FAILED, error=str(exc)
                )
                logger.error("Escalation delivery failed for %s: %s", alert.alert_id, exc)
        db.commit()
        return escalated
    finally:
        db.close()
