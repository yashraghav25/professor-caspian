"""
Background Caspian event listener — handles inbound ACK replies.
Polls events (non-blocking) instead of client.listen().
"""

from __future__ import annotations

import asyncio

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.alert_service import AlertService
from app.models.user import User
from app.caspian.client import get_caspian

logger = get_logger("caspian_listener")

_listener_active = False
_listener_task = None
_event_cursor = 0

DEMO_USER_ID = 1


async def start_caspian_listener():
    global _listener_active, _listener_task
    caspian = get_caspian()
    if not caspian.is_ready:
        logger.info("Caspian listener skipped — client not ready.")
        return
    if _listener_active:
        return
    _listener_active = True
    _listener_task = asyncio.create_task(_poll_loop())
    logger.info("Caspian inbound listener started.")


async def stop_caspian_listener():
    global _listener_active, _listener_task
    _listener_active = False
    if _listener_task:
        _listener_task.cancel()
        try:
            await _listener_task
        except asyncio.CancelledError:
            pass
    logger.info("Caspian inbound listener stopped.")


async def _poll_loop():
    global _event_cursor
    caspian = get_caspian()
    await asyncio.sleep(3)

    while _listener_active:
        try:
            events, _event_cursor = await caspian.poll_events(after_seq=_event_cursor)
            for event in events:
                if event.get("type") == "message.received":
                    await _handle_inbound(event.get("data", {}), event)
        except Exception as e:
            logger.error(f"Caspian poll error: {e}")
        await asyncio.sleep(5)


async def _handle_inbound(data: dict, event: dict):
    text = (data.get("text") or data.get("content") or "").strip().lower()
    sender = data.get("from") or data.get("sender") or ""
    conversation_id = data.get("conversation_id")

    if text not in ("ack", "acknowledge", "acknowledged"):
        # Route general inbound to agent (optional lightweight reply)
        if text and conversation_id:
            try:
                from app.agent.graph import SentinelAgent
                agent = SentinelAgent()
                reply = await agent.run(
                    DEMO_USER_ID,
                    f"The investor messaged via Caspian: '{text}'. "
                    f"Reply briefly with portfolio status or help. Keep under 200 chars.",
                )
                caspian = get_caspian()
                await caspian.reply_in_conversation(conversation_id, reply[:400])
            except Exception as e:
                logger.warning(f"Inbound agent reply failed: {e}")
        return

    logger.info(f"Caspian ACK from {sender}")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == DEMO_USER_ID).first()
        if not user:
            return
        alert_service = AlertService(db)
        active = alert_service.get_active_alerts(user.id, limit=1)
        if active:
            alert_service.acknowledge_alert(user.id, active[0].alert_id)
            logger.info(f"Acknowledged alert {active[0].alert_id} via Caspian")
            if conversation_id:
                caspian = get_caspian()
                await caspian.reply_in_conversation(
                    conversation_id, "✓ Alert acknowledged. Monitoring continues."
                )
    finally:
        db.close()
