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
        content = (data.get("text") or data.get("content") or "").strip().lower()
        if content in ("ack", "acknowledge", "acknowledged"):
            alert_service = AlertService(db)
            active = alert_service.get_active_alerts(DEMO_USER_ID, limit=1)
            if active:
                alert_service.acknowledge_alert(DEMO_USER_ID, active[0].alert_id)
                logger.info(f"Webhook ACK for alert {active[0].alert_id}")

    return {"status": "ok"}


@router.get("/caspian/status")
def caspian_status():
    """Return Caspian channel connection status."""
    from app.caspian.client import get_caspian

    caspian = get_caspian()
    return {
        "ready": caspian.is_ready,
        "email_address": caspian.email_address,
    }


@router.post("/caspian/test-daily-report")
async def test_daily_report():
    """Manually trigger the end-of-day email digest (for testing)."""
    from app.workers.daily_report_worker import _send_daily_report

    await _send_daily_report()
    return {"status": "ok", "message": "Daily report sent via Caspian email."}
