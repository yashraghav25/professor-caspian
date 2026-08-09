"""
Caspian webhook fallback — primary inbound handling is in listener.py (event polling).
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.alert_service import AlertService

logger = get_logger("caspian_handlers")
router = APIRouter()

DEMO_USER_ID = 1


@router.post("/caspian/webhook")
async def caspian_webhook(request: Request, db: Session = Depends(get_db)):
    """Optional webhook endpoint if Caspian is configured to push events here."""
    payload = await request.json()
    logger.info(f"Caspian webhook: {json.dumps(payload)[:500]}")

    event_type = payload.get("type")
    if event_type == "message.received":
        data = payload.get("data", {})
        message = data.get("message") if isinstance(data.get("message"), dict) else data
        content = (message.get("text") or message.get("content") or "").strip().lower()
        if content in ("ack", "acknowledge", "acknowledged"):
            alert_service = AlertService(db)
            active = alert_service.get_active_alerts(DEMO_USER_ID, limit=1)
            if active:
                alert_service.acknowledge_alert(DEMO_USER_ID, active[0].alert_id)
                logger.info(f"Webhook ACK for alert {active[0].alert_id}")
                message_id = message.get("id")
                if message_id:
                    try:
                        from app.caspian.client import get_caspian

                        await get_caspian().reply_to_message(
                            message_id, "✓ Alert acknowledged. Monitoring continues."
                        )
                    except Exception as exc:
                        logger.warning(f"Webhook ACK reply failed: {exc}")

    return {"status": "ok"}


@router.get("/caspian/status")
def caspian_status():
    """Return Caspian channel connection status."""
    from app.caspian.client import get_caspian

    caspian = get_caspian()
    return {
        "ready": caspian.is_ready,
        "email_address": caspian.email_address,
        "telegram_address": caspian.telegram_address,
        "telegram_ready": caspian.telegram_ready,
        "routing": {
            "WARNING": "email only",
            "HIGH": "telegram + email",
            "CRITICAL": "telegram + email",
        },
    }


@router.post("/caspian/test-daily-report")
async def test_daily_report():
    """Manually trigger the end-of-day email digest (for testing)."""
    from app.workers.daily_report_worker import _send_daily_report

    await _send_daily_report()
    return {"status": "ok", "message": "Daily report sent via Caspian email."}


@router.post("/caspian/test-telegram")
async def test_telegram():
    """Send a test HIGH alert to Telegram via Caspian send_message."""
    from app.caspian.client import get_caspian
    from app.caspian.message_builder import build_telegram_text
    from app.models.alert import Alert, AlertStatus

    caspian = get_caspian()
    if not caspian.is_ready:
        return {"status": "error", "message": "Caspian not initialized"}

    fake = Alert(
        alert_id="test",
        severity_level=AlertStatus.HIGH,
        severity_score=72,
        title="HIGH: NVDA -8.2%",
        reason="Test alert",
        ai_summary=(
            "**What happened**\nNVDA dropped 8.2% on earnings miss headline.\n\n"
            "**Portfolio impact**\n~20% portfolio exposure to NVDA.\n\n"
            "**Suggested actions**\n1. Review NVDA position size."
        ),
    )
    text = build_telegram_text(fake)
    result = await caspian.send_telegram(text)
    return {"status": "ok", "message": "Test Telegram sent.", "result": result}
