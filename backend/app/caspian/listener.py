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
from app.caspian.message_builder import build_rich_blocks

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
        # Caspian's event API is ordered; a short poll keeps Telegram commands
        # feeling conversational without a separate webhook service.
        await asyncio.sleep(1)


async def _handle_inbound(data: dict, event: dict):
    # Caspian's event shape is {type, data: {message: {...}}}. The previous
    # outer-level read made every Telegram command look blank.
    message = data.get("message") if isinstance(data.get("message"), dict) else data
    text = (message.get("text") or message.get("content") or "").strip()
    text_lower = text.lower()
    sender = message.get("from") or message.get("sender") or ""
    message_id = message.get("id")
    conversation_id = message.get("conversation_id")
    channel = message.get("channel") or data.get("channel") or event.get("channel")

    # Cache Telegram conversation for outbound alerts
    if conversation_id and channel == "telegram":
        get_caspian().set_telegram_conversation(conversation_id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == DEMO_USER_ID).first()
        if not user:
            return
        alert_service = AlertService(db)
        active = alert_service.get_active_alerts(user.id, limit=1)
        latest = active[0] if active else None

        if text_lower in ("ack", "acknowledge", "acknowledged"):
            logger.info(f"Caspian ACK from {sender}")
            if latest:
                alert_service.acknowledge_alert(user.id, latest.alert_id)
                logger.info(f"Acknowledged alert {latest.alert_id} via Caspian")
                if message_id:
                    await _reply_to_inbound(
                        message_id,
                        "✓ Alert acknowledged. SentinelAI will continue monitoring and only interrupt for a new material event.",
                    )
            return

        if text_lower in ("why", "evidence", "why?"):
            if message_id:
                reply = _build_why_reply(latest)
                await _reply_to_inbound(message_id, reply, blocks=build_rich_blocks(reply))
            return

        if text_lower in ("details", "detail", "brief"):
            if message_id:
                reply = _build_details_reply(latest)
                await _reply_to_inbound(message_id, reply, blocks=build_rich_blocks(reply))
            return

        # General inbound remains conversational, but the explicit commands
        # above are deterministic and easy to demonstrate in a live pitch.
        if text and message_id:
            try:
                from app.agent.graph import SentinelAgent
                agent = SentinelAgent()
                reply = await agent.answer_investor_question(DEMO_USER_ID, text)
                await _reply_to_inbound(message_id, reply[:1200], blocks=build_rich_blocks(reply))
            except Exception as e:
                logger.warning(f"Inbound agent reply failed: {e}")
    finally:
        db.close()


async def _reply_to_inbound(
    message_id: str, text: str, blocks: list[dict] | None = None
) -> None:
    """Best-effort response: a reply failure must not stop later event handling."""
    try:
        await get_caspian().reply_to_message(message_id, text, blocks=blocks)
    except Exception as exc:
        logger.error("Caspian reply failed for inbound message %s: %s", message_id, exc)


def _build_why_reply(alert) -> str:
    """Return a concise, evidence-led response for the WHY Caspian command."""
    if not alert:
        return "No active SentinelAI incident right now. Your portfolio is still being monitored."
    return (
        f"WHY THIS ALERT\n"
        f"{alert.title}\n"
        f"Severity: {alert.severity_level} ({alert.severity_score:.0f}/100)\n"
        f"Evidence: {(alert.reason or 'A material portfolio event was detected.')[:210]}\n"
        "Reply DETAILS for the full incident brief or ACK to acknowledge."
    )[:700]


def _build_details_reply(alert) -> str:
    """Return the full incident narrative without giving trading instructions."""
    if not alert:
        return "No active SentinelAI incident right now. Your portfolio is still being monitored."
    narrative = alert.ai_summary or alert.reason or "Analysis is still being prepared."
    return (
        f"INCIDENT BRIEF\n{alert.title}\n\n{narrative}\n\n"
        "This is monitoring context, not financial advice. Reply ACK when you have seen it."
    )[:1200]
