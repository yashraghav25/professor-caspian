"""
Routes alert notifications through Caspian by severity:
- WARNING  → email only (small alert)
- HIGH     → telegram + email (instant response plus durable record)
- CRITICAL → telegram + email
"""

from __future__ import annotations

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.alert import Alert, AlertStatus
from app.models.notification import Notification, NotificationStatus
from app.services.notification_service import NotificationService
from app.caspian.client import get_caspian
from app.caspian.message_builder import (
    build_email_subject,
    build_email_plain,
    build_email_html,
    build_telegram_text,
    build_telegram_blocks,
    build_daily_report_html,
)

logger = get_logger("caspian_notifications")


def _channels_for_severity(severity_level: AlertStatus) -> list[str]:
    if severity_level == AlertStatus.CRITICAL:
        return ["telegram", "email"]
    if severity_level == AlertStatus.HIGH:
        return ["telegram", "email"]
    if severity_level == AlertStatus.WARNING:
        return ["email"]
    return []


async def dispatch_alert_via_caspian(alert: Alert) -> None:
    """Send notifications via Caspian after AI analysis is ready."""
    db = SessionLocal()
    try:
        service = NotificationService(db)
        db_alert = db.query(Alert).filter(Alert.alert_id == alert.alert_id).first()
        if not db_alert:
            return

        channels = _channels_for_severity(db_alert.severity_level)
        if not channels:
            logger.info(f"No notification channels for severity {db_alert.severity_level}")
            return

        logger.info(
            f"Dispatching {channels} for {db_alert.severity_level.value} alert {db_alert.alert_id}"
        )

        for ch in channels:
            notif = Notification(
                alert_id=db_alert.alert_id,
                channel=ch,
                status=NotificationStatus.PENDING,
            )
            db.add(notif)
            db.flush()

            try:
                msg_id = await _send_on_channel(ch, db_alert)
                service.update_notification_status(
                    notif.id, NotificationStatus.SENT, message_id=msg_id
                )
                logger.info(f"Caspian {ch} sent for alert {db_alert.alert_id}")
            except Exception as e:
                logger.error(f"Caspian {ch} failed: {e}")
                service.update_notification_status(
                    notif.id, NotificationStatus.FAILED, error=str(e)
                )

        db.commit()
    finally:
        db.close()


async def _send_on_channel(channel: str, alert: Alert) -> str | None:
    caspian = get_caspian()
    if not caspian.is_ready:
        raise RuntimeError("Caspian not initialized")

    if channel == "email":
        subject = build_email_subject(alert)
        plain = build_email_plain(alert)
        html = build_email_html(alert)
        result = await caspian.send_email(
            settings.investor_notify_email, subject, plain, html
        )
        return result.get("id") or result.get("status")

    if channel == "telegram":
        text = build_telegram_text(alert)
        result = await caspian.send_telegram(text, blocks=build_telegram_blocks(alert))
        return result.get("id") or result.get("status")

    raise ValueError(f"Unknown channel: {channel}")


async def send_daily_report_email(subject: str, body: str) -> None:
    """End-of-day portfolio digest — always email with proper formatting."""
    caspian = get_caspian()
    if not caspian.is_ready:
        raise RuntimeError("Caspian not initialized")

    subj, html = build_daily_report_html(subject, body)
    await caspian.send_email(settings.investor_notify_email, subj, body, html)
    logger.info("Daily report email sent via Caspian.")
