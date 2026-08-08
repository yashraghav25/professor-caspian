"""
Severity Service — PRD Sections 30, 31, 50.
Calculates deterministic severity scores and levels.
"""

from typing import Dict, Any, Tuple
from app.core.config import settings
from app.models.alert import AlertStatus


class SeverityService:
    
    @staticmethod
    def calculate_severity(
        event_type: str, 
        impact_data: Dict[str, Any], 
        event_payload: Dict[str, Any]
    ) -> Tuple[float, AlertStatus]:
        """
        Calculate severity score (0-100) and corresponding AlertStatus.
        """
        score = 0.0
        
        if event_type == "PRICE_MOVEMENT":
            # 1. Price Movement (up to 30 points)
            change_abs = abs(event_payload.get("change_percent", 0.0))
            if change_abs >= settings.critical_price_change:
                score += settings.weight_price_movement
            elif change_abs >= settings.high_price_change:
                score += settings.weight_price_movement * 0.7
            elif change_abs >= settings.warning_price_change:
                score += settings.weight_price_movement * 0.4
                
            # 2. Velocity (simplified for MVP - base it on volume or static for now)
            # In a real app, we'd check previous events for this symbol within a timeframe
            volume = event_payload.get("volume_ratio", 1.0)
            if volume > 3.0:
                score += settings.weight_velocity
            elif volume > 1.5:
                score += settings.weight_velocity * 0.5
                
        elif event_type == "NEWS":
            # 1. News Impact (up to 20 points)
            ai_analysis = event_payload.get("ai_analysis", {})
            impact_level = ai_analysis.get("impact", "low").lower()
            
            if impact_level == "high":
                score += settings.weight_news_impact
            elif impact_level == "medium":
                score += settings.weight_news_impact * 0.5
                
            # 2. Confidence (up to 10 points)
            confidence = ai_analysis.get("confidence", 0.0)
            score += confidence * settings.weight_confidence

        # 3. Portfolio Exposure (up to 25 points)
        exposure = impact_data.get("exposure_percent", 0.0)
        if exposure >= 20.0:
            score += settings.weight_portfolio_exposure
        elif exposure >= 10.0:
            score += settings.weight_portfolio_exposure * 0.6
        elif exposure > 0:
            score += settings.weight_portfolio_exposure * 0.3

        # Cap at 100
        score = min(100.0, score)
        
        # Map score to AlertStatus
        status = SeverityService.get_status_from_score(score)
        
        return score, status

    @staticmethod
    def get_status_from_score(score: float) -> AlertStatus:
        if score <= settings.info_max:
            return AlertStatus.NORMAL  # Normal/Info
        elif score <= settings.low_max:
            return AlertStatus.WATCHING
        elif score <= settings.warning_max:
            return AlertStatus.WARNING
        elif score <= settings.high_max:
            return AlertStatus.HIGH
        else:
            return AlertStatus.CRITICAL
