"""
Simulation Engine — PRD Sections 37, 38, 63, 64.
Executes pre-defined scenarios deterministically.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.database import SessionLocal
from app.schemas.event import EventBase
from app.services.event_service import EventService
from app.simulation.scenarios import SCENARIOS, get_scenario_events

logger = get_logger("simulation_engine")

DEMO_USER_ID = 1


class SimulationEngine:
    """Singleton simulation engine to handle asynchronous event injection."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationEngine, cls).__new__(cls)
            cls._instance._running = False
            cls._instance._task = None
            cls._instance._current_scenario = None
            cls._instance._progress = 0
            cls._instance._latest_event = None
            cls._instance._latest_ai_summary = None
            cls._instance._agent_busy = False
        return cls._instance

    @property
    def is_running(self) -> bool:
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Get the current simulation status for the frontend control panel."""
        return {
            "running": self._running,
            "scenario": self._current_scenario,
            "progress": self._progress,
            "latest_event": self._latest_event,
            "latest_ai_summary": self._latest_ai_summary,
            "agent_busy": self._agent_busy,
        }

    async def start_scenario(self, scenario_name: str, db: Session):
        """Start a predefined scenario in the background."""
        if self._running:
            raise ValueError(f"A scenario is already running: {self._current_scenario}")

        if scenario_name not in SCENARIOS:
            raise ValueError(f"Scenario not found: {scenario_name}")

        self._running = True
        self._current_scenario = scenario_name
        self._progress = 0
        self._latest_event = None
        self._latest_ai_summary = None
        self._agent_busy = False

        # rapid_crash rotates through 10 unique scenarios each call
        scenario = (
            get_scenario_events(scenario_name)
            if scenario_name == "rapid_crash"
            else SCENARIOS[scenario_name]
        )
        # Adapt crash symbols/prices to the user's live holdings
        scenario = self._adapt_scenario_to_portfolio(scenario, db)
        logger.info(f"Starting scenario: {scenario_name} with {len(scenario)} events")

        # Own session for background task (request session may close)
        self._task = asyncio.create_task(self._run_events(scenario))

    def _adapt_scenario_to_portfolio(
        self, scenario: List[Dict[str, Any]], db: Session
    ) -> List[Dict[str, Any]]:
        """
        Remap scenario symbols onto the user's holdings and convert absolute
        crash prices into % moves off the live price so the dashboard crashes.
        """
        from app.models.holding import Holding
        from app.models.portfolio import Portfolio

        portfolio = db.query(Portfolio).filter(Portfolio.user_id == DEMO_USER_ID).first()
        if not portfolio:
            return scenario

        holdings = (
            db.query(Holding)
            .filter(Holding.portfolio_id == portfolio.id, Holding.symbol != "CASH")
            .all()
        )
        if not holdings:
            return scenario

        held = {h.symbol.upper(): h for h in holdings}
        held_symbols = list(held.keys())

        # Map each unique scenario symbol onto a held symbol (prefer exact match)
        scenario_symbols = []
        for step in scenario:
            sym = step.get("event", {}).get("symbol")
            if sym and sym.upper() not in scenario_symbols:
                scenario_symbols.append(sym.upper())

        symbol_map: Dict[str, str] = {}
        unused = [s for s in held_symbols if s not in scenario_symbols]
        for i, sym in enumerate(scenario_symbols):
            if sym in held:
                symbol_map[sym] = sym
            elif unused:
                symbol_map[sym] = unused.pop(0)
            else:
                symbol_map[sym] = held_symbols[i % len(held_symbols)]

        adapted: List[Dict[str, Any]] = []
        for step in scenario:
            event = dict(step["event"])
            original_sym = event.get("symbol")
            if original_sym:
                mapped = symbol_map.get(original_sym.upper(), original_sym.upper())
                event["symbol"] = mapped
                # Drop hardcoded absolute prices — engine will apply % to live price
                event.pop("price", None)
                event.pop("previous_price", None)

            adapted.append({"delay_seconds": step.get("delay_seconds", 0), "event": event})

        logger.info(f"Adapted scenario symbols: {symbol_map}")
        return adapted

    async def stop(self):
        """Stop the currently running scenario."""
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._current_scenario = None
            self._progress = 0
            self._agent_busy = False
            logger.info("Simulation stopped")

    async def reset(self, db: Session):
        """Reset the simulation state (stop and clear events)."""
        await self.stop()
        logger.info("Simulation reset requested")

    async def inject_custom_event(self, event_data: dict, db: Session):
        """Inject a single custom event immediately."""
        event_service = EventService(db)

        event_id = event_service.generate_event_id()
        now = datetime.now(timezone.utc)

        event_type = event_data.get("type", "PRICE_MOVEMENT")

        if event_type == "PRICE_MOVEMENT":
            payload = {
                "price": event_data.get("price", 100.0),
                "previous_price": event_data.get("previous_price", 100.0),
                "change_percent": event_data.get("change_percent", 0.0),
                "volume_ratio": 1.0,
            }
        else:
            payload = {
                "headline": event_data.get("headline", "Custom News"),
                "summary": event_data.get("summary", ""),
                "source_name": "Custom Injector",
                "ai_analysis": {
                    "impact": "high",
                    "confidence": 0.9,
                    "sentiment": "negative",
                    "entities": [event_data.get("symbol")] if event_data.get("symbol") else [],
                    "reason": event_data.get("summary") or event_data.get("headline", ""),
                },
            }

        event = EventBase(
            event_id=event_id,
            event_type=event_type,
            source="simulation",
            symbol=event_data.get("symbol"),
            payload=payload,
            occurred_at=now,
        )

        event_service.ingest_event(event)
        self._latest_event = event_type
        await self._process_event(event, db)

    async def _run_events(self, scenario: List[Dict[str, Any]]):
        """Execute the event sequence with proper delays."""
        total_events = len(scenario)

        try:
            for i, step in enumerate(scenario):
                if not self._running:
                    break

                delay = step.get("delay_seconds", 0)
                if delay > 0:
                    await asyncio.sleep(delay)

                if not self._running:
                    break

                db = SessionLocal()
                try:
                    event_service = EventService(db)
                    event_data = step["event"]
                    event_type = event_data["type"]
                    event_id = event_service.generate_event_id()

                    if event_type == "PRICE_MOVEMENT":
                        payload = {
                            "change_percent": event_data.get("change_percent", 0.0),
                            "volume_ratio": event_data.get("volume_ratio", 1.0),
                        }
                        if "price" in event_data:
                            payload["price"] = event_data["price"]
                        if "previous_price" in event_data:
                            payload["previous_price"] = event_data["previous_price"]
                    else:
                        payload = {
                            "headline": event_data.get("headline", "News"),
                            "summary": event_data.get("summary", ""),
                            "source_name": "Simulation News Feed",
                            # Seed high-impact analysis so news severity scores fire
                            "ai_analysis": {
                                "impact": "high",
                                "confidence": 0.92,
                                "sentiment": "negative",
                                "entities": (
                                    [event_data["symbol"]] if event_data.get("symbol") else []
                                ),
                                "reason": event_data.get("summary")
                                or event_data.get("headline", ""),
                            },
                        }

                    event = EventBase(
                        event_id=event_id,
                        event_type=event_type,
                        source="simulation",
                        symbol=event_data.get("symbol"),
                        payload=payload,
                        occurred_at=datetime.now(timezone.utc),
                    )

                    logger.info(f"Simulation injecting: {event_type} for {event.symbol}")
                    event_service.ingest_event(event)
                    await self._process_event(event, db)

                    self._latest_event = f"{event_type} {event.symbol if event.symbol else ''}"
                    self._progress = int(((i + 1) / total_events) * 100)
                finally:
                    db.close()

        except asyncio.CancelledError:
            logger.info("Scenario cancelled")
        except Exception as e:
            logger.error(f"Error running scenario: {e}", exc_info=True)
        finally:
            self._running = False
            self._agent_busy = False
            if self._progress == 100:
                logger.info(f"Scenario {self._current_scenario} completed")

    async def _process_event(self, event: EventBase, db: Session):
        """
        Full processing pipeline: Impact -> Severity -> Alert -> Agent.
        """
        from app.services.impact_service import ImpactService
        from app.services.severity_service import SeverityService
        from app.services.alert_service import AlertService
        from app.services.portfolio_service import PortfolioService
        from app.agent.graph import SentinelAgent
        from app.models.alert import AlertStatus
        from app.models.holding import Holding

        try:
            # 0. Update holding price from % move off live price
            if event.event_type == "PRICE_MOVEMENT" and event.symbol:
                change_pct = float(event.payload.get("change_percent", 0.0))
                portfolio_service = PortfolioService(db)
                portfolio = portfolio_service.get_portfolio(DEMO_USER_ID)
                holding = (
                    db.query(Holding)
                    .filter(
                        Holding.portfolio_id == portfolio.id,
                        Holding.symbol == event.symbol.upper(),
                    )
                    .first()
                )
                if holding:
                    base = holding.current_price or holding.average_price or 100.0
                    new_price = event.payload.get("price")
                    if new_price is None:
                        new_price = round(base * (1 + change_pct / 100), 4)
                    event.payload["previous_price"] = float(base)
                    event.payload["price"] = float(new_price)
                    holding.current_price = float(new_price)
                    db.commit()
                    logger.info(
                        f"Updated {event.symbol} price ${base:.2f} → ${new_price:.2f} ({change_pct:+.1f}%)"
                    )

            # 1. Impact
            impact_service = ImpactService(db)
            if event.event_type == "PRICE_MOVEMENT":
                impact = impact_service.calculate_market_impact(DEMO_USER_ID, event)
            else:
                impact = impact_service.calculate_news_impact(DEMO_USER_ID, event)

            logger.info(f"Impact calculated: exposure={impact.get('exposure_percent', 0):.1f}%")

            # 2. Severity
            score, severity_level = SeverityService.calculate_severity(
                event.event_type, impact, event.payload
            )
            logger.info(f"Severity: {severity_level} (score={score:.1f})")

            # 3. Alert if threshold crossed
            if severity_level in (AlertStatus.WARNING, AlertStatus.HIGH, AlertStatus.CRITICAL):
                portfolio_service_alert = PortfolioService(db)
                portfolio = portfolio_service_alert.get_portfolio(DEMO_USER_ID)

                symbol = event.symbol or "Portfolio"
                change = event.payload.get("change_percent", 0.0)
                headline = event.payload.get("headline")
                title = (
                    f"{severity_level.value.upper()}: {headline[:80]}"
                    if headline
                    else f"{severity_level.value.upper()}: {symbol} {change:+.1f}%"
                )
                reason = (
                    f"{event.event_type} event for {symbol}. "
                    f"Portfolio exposure: {impact.get('exposure_percent', 0):.1f}%. "
                    f"Severity score: {score:.0f}/100."
                )

                alert_service = AlertService(db)
                alert = alert_service.process_alert_transition(
                    user_id=DEMO_USER_ID,
                    portfolio_id=portfolio.id,
                    event_id=event.event_id,
                    severity_score=score,
                    severity_level=severity_level,
                    title=title,
                    reason=reason,
                )

                # 4. Always run agent on new/escalated alerts; also force-run once
                #    for the first significant demo event even if cooldown suppressed
                #    a duplicate (attach summary to the recent alert).
                target_alert = alert
                if not target_alert:
                    target_alert = alert_service.get_latest_active_alert(DEMO_USER_ID)

                if target_alert and not self._latest_ai_summary:
                    await self._run_agent_analysis(
                        db=db,
                        alert=target_alert,
                        event=event,
                        impact=impact,
                        severity_level=severity_level,
                        score=score,
                    )
                elif target_alert and alert:
                    # Escalation — refresh analysis
                    await self._run_agent_analysis(
                        db=db,
                        alert=target_alert,
                        event=event,
                        impact=impact,
                        severity_level=severity_level,
                        score=score,
                    )

        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}", exc_info=True)

    async def _run_agent_analysis(
        self,
        db: Session,
        alert,
        event: EventBase,
        impact: Dict[str, Any],
        severity_level,
        score: float,
    ):
        """Invoke SentinelAgent and persist narrative + suggested actions."""
        from app.agent.graph import SentinelAgent
        from app.models.alert import Alert

        self._agent_busy = True
        try:
            headline = event.payload.get("headline")
            summary = event.payload.get("summary")
            change = event.payload.get("change_percent", 0.0)
            symbol = event.symbol or "the portfolio"

            agent = SentinelAgent()
            agent_message = f"""
A portfolio alert just fired during live monitoring. Produce an investor-facing brief.

ALERT
- Severity: {severity_level.value if hasattr(severity_level, 'value') else severity_level}
- Score: {score:.0f}/100
- Symbol: {symbol}
- Event type: {event.event_type}
- Price change: {change:+.1f}%
- Portfolio exposure: {impact.get('exposure_percent', 0):.1f}%
- Estimated $ impact: {impact.get('dollar_impact', impact.get('estimated_loss', 'n/a'))}
- Headline: {headline or 'n/a'}
- News summary: {summary or 'n/a'}

INSTRUCTIONS
1. Use get_portfolio_summary to check current holdings and P/L.
2. Write a clear narrative of WHAT happened and WHY it matters to THIS portfolio.
3. End with 2-3 concrete suggested actions the investor should consider now.
4. Do NOT just repeat the severity score. Be specific and actionable.
"""
            analysis = await agent.run(DEMO_USER_ID, agent_message)
            if not analysis or not str(analysis).strip():
                analysis = self._fallback_summary(event, impact, severity_level, score)

            # Persist on alert row
            db_alert = db.query(Alert).filter(Alert.alert_id == alert.alert_id).first()
            if db_alert:
                db_alert.ai_summary = str(analysis).strip()
                db.commit()

            self._latest_ai_summary = str(analysis).strip()
            logger.info(f"Agent analysis persisted on {alert.alert_id}: {analysis[:120]}...")

            # Dispatch Caspian notifications (email / telegram by severity)
            if db_alert:
                from app.caspian.notification_adapter import dispatch_alert_via_caspian
                await dispatch_alert_via_caspian(db_alert)
        except Exception as e:
            logger.error(f"Agent analysis failed: {e}", exc_info=True)
            fallback = self._fallback_summary(event, impact, severity_level, score)
            try:
                from app.models.alert import Alert

                db_alert = db.query(Alert).filter(Alert.alert_id == alert.alert_id).first()
                if db_alert:
                    db_alert.ai_summary = fallback
                    db.commit()
                self._latest_ai_summary = fallback
            except Exception:
                self._latest_ai_summary = fallback
        finally:
            self._agent_busy = False

    def _fallback_summary(self, event, impact, severity_level, score) -> str:
        symbol = event.symbol or "your portfolio"
        change = event.payload.get("change_percent", 0.0)
        headline = event.payload.get("headline")
        level = severity_level.value if hasattr(severity_level, "value") else str(severity_level)
        what = headline or f"{symbol} moved {change:+.1f}% in a sharp, high-volume move."
        return (
            f"What happened: {what} This registers as a {level} event "
            f"(score {score:.0f}/100) with ~{impact.get('exposure_percent', 0):.1f}% portfolio exposure.\n\n"
            f"Suggested actions:\n"
            f"1. Review your {symbol} position size and overall portfolio concentration.\n"
            f"2. Decide whether to hold, trim, or hedge based on your risk tolerance — avoid panic selling into the first print.\n"
            f"3. Set or tighten a stop / alert threshold and watch for a second-leg move over the next session."
        )
