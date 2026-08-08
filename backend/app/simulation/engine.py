"""
Simulation Engine — PRD Sections 37, 38, 63, 64.
Executes pre-defined scenarios deterministically.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.schemas.event import EventBase, PriceEventPayload, NewsEventPayload
from app.services.event_service import EventService
from app.simulation.scenarios import SCENARIOS, get_scenario_events

logger = get_logger("simulation_engine")

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
            "latest_event": self._latest_event
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
        
        # rapid_crash rotates through 10 unique scenarios each call
        scenario = get_scenario_events(scenario_name) if scenario_name == "rapid_crash" else SCENARIOS[scenario_name]
        logger.info(f"Starting scenario: {scenario_name} with {len(scenario)} events")
        
        # Start background task
        self._task = asyncio.create_task(self._run_events(scenario, db))
        
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
                "volume_ratio": 1.0
            }
        else:
            payload = {
                "headline": event_data.get("headline", "Custom News"),
                "summary": event_data.get("summary", ""),
                "source_name": "Custom Injector",
            }
            
        event = EventBase(
            event_id=event_id,
            event_type=event_type,
            source="simulation",
            symbol=event_data.get("symbol"),
            payload=payload,
            occurred_at=now
        )
        
        event_service.ingest_event(event)
        self._latest_event = event_type
        
        # Trigger full processing pipeline
        await self._process_event(event, db)
        
    async def _run_events(self, scenario: List[Dict[str, Any]], db: Session):
        """Execute the event sequence with proper delays."""
        total_events = len(scenario)
        event_service = EventService(db)
        
        try:
            for i, step in enumerate(scenario):
                if not self._running:
                    break
                    
                delay = step.get("delay_seconds", 0)
                if delay > 0:
                    await asyncio.sleep(delay)
                    
                if not self._running:
                    break
                    
                # Build and inject event
                event_data = step["event"]
                event_type = event_data["type"]
                event_id = event_service.generate_event_id()
                
                if event_type == "PRICE_MOVEMENT":
                    payload = {
                        "price": event_data.get("price", 100.0),
                        "previous_price": event_data.get("previous_price", 100.0),
                        "change_percent": event_data.get("change_percent", 0.0),
                        "volume_ratio": event_data.get("volume_ratio", 1.0)
                    }
                else:
                    payload = {
                        "headline": event_data.get("headline", "News"),
                        "summary": event_data.get("summary", ""),
                        "source_name": "Simulation News Feed",
                    }
                
                event = EventBase(
                    event_id=event_id,
                    event_type=event_type,
                    source="simulation",
                    symbol=event_data.get("symbol"),
                    payload=payload,
                    occurred_at=datetime.now(timezone.utc)
                )
                
                logger.info(f"Simulation injecting: {event_type} for {event.symbol}")
                event_service.ingest_event(event)
                
                # Trigger full processing pipeline
                await self._process_event(event, db)
                
                self._latest_event = f"{event_type} {event.symbol if event.symbol else ''}"
                self._progress = int(((i + 1) / total_events) * 100)
                
        except asyncio.CancelledError:
            logger.info("Scenario cancelled")
        except Exception as e:
            logger.error(f"Error running scenario: {e}")
        finally:
            self._running = False
            if self._progress == 100:
                logger.info(f"Scenario {self._current_scenario} completed")

    async def _process_event(self, event: EventBase, db: Session):
        """
        Full processing pipeline: Impact -> Severity -> Alert -> Agent.
        This is the core of SentinelAI's autonomous monitoring.
        """
        from app.services.impact_service import ImpactService
        from app.services.severity_service import SeverityService
        from app.services.alert_service import AlertService
        from app.services.portfolio_service import PortfolioService
        from app.agent.graph import SentinelAgent
        from app.models.alert import AlertStatus

        DEMO_USER_ID = 1

        try:
            # 0. Update holding price in DB so P/L is live on the frontend
            if event.event_type == "PRICE_MOVEMENT" and event.symbol:
                new_price = event.payload.get("price")
                change_pct = event.payload.get("change_percent", 0.0)
                if new_price is None:
                    # Derive from change_percent if absolute price not provided
                    from app.models.holding import Holding
                    portfolio_service = PortfolioService(db)
                    portfolio = portfolio_service.get_portfolio(DEMO_USER_ID)
                    holding = db.query(Holding).filter(
                        Holding.portfolio_id == portfolio.id,
                        Holding.symbol == event.symbol.upper()
                    ).first()
                    if holding:
                        base = holding.current_price or holding.average_price
                        new_price = round(base * (1 + change_pct / 100), 4)
                if new_price:
                    from app.models.holding import Holding
                    portfolio_service = PortfolioService(db)
                    portfolio = portfolio_service.get_portfolio(DEMO_USER_ID)
                    holding = db.query(Holding).filter(
                        Holding.portfolio_id == portfolio.id,
                        Holding.symbol == event.symbol.upper()
                    ).first()
                    if holding:
                        holding.current_price = new_price
                        db.commit()
                        logger.info(f"Updated {event.symbol} price to ${new_price:.2f} ({change_pct:+.1f}%)")

            # 1. Calculate impact on portfolio
            impact_service = ImpactService(db)
            if event.event_type == "PRICE_MOVEMENT":
                impact = impact_service.calculate_market_impact(DEMO_USER_ID, event)
            else:
                impact = impact_service.calculate_news_impact(DEMO_USER_ID, event)

            logger.info(f"Impact calculated: exposure={impact.get('exposure_percent', 0):.1f}%")

            # 2. Calculate severity score
            score, severity_level = SeverityService.calculate_severity(
                event.event_type, impact, event.payload
            )
            logger.info(f"Severity: {severity_level} (score={score:.1f})")

            # 3. Only create alert if it crosses a threshold worth notifying about
            if severity_level in (AlertStatus.WARNING, AlertStatus.HIGH, AlertStatus.CRITICAL):
                portfolio_service_alert = PortfolioService(db)
                portfolio = portfolio_service_alert.get_portfolio(DEMO_USER_ID)

                symbol = event.symbol or "Portfolio"
                change = event.payload.get("change_percent", 0.0)
                title = f"{severity_level.value.upper()}: {symbol} {change:+.1f}%"
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

                # 4. Invoke the LLM agent to analyse the alert via Groq
                if alert:
                    logger.info(f"Alert created: {alert.alert_id}. Invoking agent...")
                    agent = SentinelAgent()
                    agent_message = (
                        f"A new {severity_level.value} alert has been triggered: {title}. "
                        f"{reason} Please analyse this and summarise what the investor should know."
                    )
                    analysis = await agent.run(DEMO_USER_ID, agent_message)
                    logger.info(f"Agent analysis complete: {analysis[:120]}...")

        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}", exc_info=True)
