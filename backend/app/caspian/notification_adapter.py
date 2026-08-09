"""
Routes alert notifications through Caspian by severity:
- WARNING  → email (small alert)
- HIGH     → telegram (instant)
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
from app.agent.graph import SentinelAgent

logger = get_logger("caspian_notifications")

DEMO_USER_ID = 1


def _channels_for_severity(severity_level: AlertStatus) -> list[str]:
    if severity_level == AlertStatus.CRITICAL:
        return ["telegram", "email"]
    if severity_level == AlertStatus.HIGH:
        return ["telegram"]
    if severity_level == AlertStatus.WARNING:
        return ["email"]
    return []


def _fallback_message(alert: Alert, channel: str) -> str:
    body = alert.ai_summary or alert.reason or alert.title
    if channel == "telegram":
        first_line = body.split("\n")[0][:200]
        return (
            f"⚠️ {alert.severity_level.value} — {alert.title}\n"
            f"{first_line}\n"
            f"Reply ACK to dismiss."
        )
    return (
        f"SentinelAI {alert.severity_level.value} Alert\n\n"
        f"{alert.title}\n\n"
        f"{body[:600]}\n\n"
        f"Reply ACK to acknowledge."
    )


async def dispatch_alert_via_caspian(alert: Alert) -> None:
    """Queue + send notifications for an alert after AI analysis is ready."""
    db = SessionLocal()
    try:
        service = NotificationService(db)
        db_alert = db.query(Alert).filter(Alert.alert_id == alert.alert_id).first()
        if not db_alert:
            return

        channels = _channels_for_severity(db_alert.severity_level)
        if not channels:
            return

        # Compose short channel-specific messages via agent
        agent = SentinelAgent()
        messages: dict[str, str] = {}
        summary = db_alert.ai_summary or db_alert.reason or db_alert.title
        for ch in channels:
            try:
                messages[ch] = await agent.compose_notification(
                    summary=summary,
                    severity=str(db_alert.severity_level.value),
                    channel=ch,
                    title=db_alert.title,
                )
            except Exception as e:
                logger.warning(f"Agent compose failed for {ch}: {e}")
                messages[ch] = _fallback_message(db_alert, ch)

        for ch in channels:
            notif = Notification(
                alert_id=db_alert.alert_id,
                channel=ch,
                status=NotificationStatus.PENDING,
            )
            db.add(notif)
            db.flush()

            try:
                msg_id = await _send_on_channel(ch, messages[ch])
                service.update_notification_status(
                    notif.id, NotificationStatus.SENT, message_id=msg_id
                )
                logger.info(f"Sent {ch} notification for alert {db_alert.alert_id}")
            except Exception as e:
                logger.error(f"Failed {ch} notification: {e}")
                service.update_notification_status(
                    notif.id, NotificationStatus.FAILED, error=str(e)
                )

        db.commit()
    finally:
        db.close()


async def _send_on_channel(channel: str, text: str) -> str | None:
    caspian = get_caspian()
    if not caspian.is_ready:
        raise RuntimeError("Caspian not initialized")

    if channel == "email":
        recipient = settings.investor_notify_email
        result = await caspian.send_email(recipient, text)
        return result.get("id") or result.get("status")

    if channel == "telegram":
        chat_id = settings.investor_telegram_chat_id
        if not chat_id:
            raise RuntimeError(
                "INVESTOR_TELEGRAM_CHAT_ID not set — message your Telegram bot first, "
                "then add the chat id to .env"
            )
        result = await caspian.send_telegram(chat_id, text)
        return result.get("id") or result.get("status")

    raise ValueError(f"Unknown channel: {channel}")


async def send_daily_report_email(subject: str, body: str) -> None:
    """End-of-day portfolio digest — always email."""
    caspian = get_caspian()
    if not caspian.is_ready:
        raise RuntimeError("Caspian not initialized")

    full_text = f"{subject}\n\n{body}"
    await caspian.send_email(settings.investor_notify_email, full_text)
    logger.info("Daily report email queued via Caspian.")
