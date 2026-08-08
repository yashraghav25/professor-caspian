"""
Impact Service — PRD Sections 25, 27, 50.
Calculates portfolio exposure and impact based on events.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.logging import get_logger
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.schemas.event import EventBase
from app.services.portfolio_service import PortfolioService

logger = get_logger("impact_service")


class ImpactService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)

    def calculate_market_impact(self, user_id: int, event: EventBase) -> Dict[str, Any]:
        """
        Calculate impact of a market event on a portfolio.
        Returns impact metrics.
        """
        symbol = event.symbol
        if not symbol:
            return {"exposure_percent": 0.0, "impact_percent": 0.0}

        payload = event.payload
        price_change_percent = payload.get("change_percent", 0.0)

        exposure_percent = self.portfolio_service.get_portfolio_weight(user_id, symbol) * 100
        impact_percent = (exposure_percent / 100) * price_change_percent

        return {
            "exposure_percent": exposure_percent,
            "impact_percent": impact_percent,
            "affected_symbols": [symbol]
        }

    def calculate_news_impact(self, user_id: int, event: EventBase) -> Dict[str, Any]:
        """
        Calculate impact of a news event based on LLM analysis.
        Matches entities/sectors to portfolio holdings.
        """
        payload = event.payload
        ai_analysis = payload.get("ai_analysis", {})
        
        entities = [e.upper() for e in ai_analysis.get("entities", [])]
        # (For MVP, we just match by entity symbols directly)
        
        portfolio = self.portfolio_service.get_portfolio(user_id)
        holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        
        affected_holdings = [h for h in holdings if h.symbol.upper() in entities]
        affected_symbols = [h.symbol for h in affected_holdings]
        
        total_value = sum(h.position_value for h in holdings)
        affected_value = sum(h.position_value for h in affected_holdings)
        
        exposure_percent = (affected_value / total_value * 100) if total_value > 0 else 0.0
        
        return {
            "exposure_percent": exposure_percent,
            "impact_percent": 0.0,  # Qualitative impact is used in severity scoring, not deterministic PNL
            "affected_symbols": affected_symbols
        }
