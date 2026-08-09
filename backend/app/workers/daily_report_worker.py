"""
End-of-day portfolio digest — emailed via Caspian once per day.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, date

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.portfolio_service import PortfolioService
from app.services.event_service import EventService
from app.agent.graph import SentinelAgent
from app.caspian.notification_adapter import send_daily_report_email

logger = get_logger("daily_report_worker")

DEMO_USER_ID = 1

_worker_active = False
_worker_task = None
_last_report_date: date | None = None


async def start_daily_report_worker():
    global _worker_active, _worker_task
    if _worker_active:
        return
    _worker_active = True
    _worker_task = asyncio.create_task(_schedule_loop())
    logger.info(f"Daily report worker started (hour={settings.daily_report_hour} UTC).")


async def stop_daily_report_worker():
    global _worker_active, _worker_task
    _worker_active = False
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass


async def _schedule_loop():
    await asyncio.sleep(10)
    while _worker_active:
        try:
            now = datetime.now(timezone.utc)
            if now.hour == settings.daily_report_hour and _should_send_today(now.date()):
                await _send_daily_report()
        except Exception as e:
            logger.error(f"Daily report error: {e}")
        await asyncio.sleep(3600)  # check hourly


def _should_send_today(today: date) -> bool:
    global _last_report_date
    if _last_report_date == today:
        return False
    return True


async def _send_daily_report():
    global _last_report_date
    db = SessionLocal()
    try:
        portfolio_svc = PortfolioService(db)
        event_svc = EventService(db)

        try:
            portfolio = portfolio_svc.get_portfolio_summary(DEMO_USER_ID)
        except Exception:
            logger.info("No portfolio for daily report — skipping.")
            return

        news = event_svc.get_recent_news_events(limit=8)
        news_lines = [
            f"- {n.headline}" + (f" ({n.source})" if n.source else "")
            for n in news[:5]
        ]

        holdings_lines = [
            f"- {h.symbol}: ${h.current_price:.2f} ({h.change_percent:+.1f}%), "
            f"P/L ${h.unrealized_pnl:,.0f}, weight {h.weight:.1f}%"
            for h in portfolio.holdings
            if h.symbol.upper() != "CASH"
        ]

        agent = SentinelAgent()
        digest = await agent.compose_daily_report(
            portfolio_total=portfolio.total_value,
            portfolio_pnl=portfolio.total_pnl,
            portfolio_pnl_pct=portfolio.total_pnl_percent,
            holdings_summary="\n".join(holdings_lines),
            news_summary="\n".join(news_lines) or "No major headlines today.",
        )

        subject = f"SentinelAI Daily — ${portfolio.total_value:,.0f} ({portfolio.total_pnl_percent:+.1f}%)"
        await send_daily_report_email(subject, digest)
        _last_report_date = datetime.now(timezone.utc).date()
        logger.info("Daily report sent.")
    finally:
        db.close()
