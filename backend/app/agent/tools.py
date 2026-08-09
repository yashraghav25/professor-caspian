"""
Agent Tools — PRD Section 45.
Tools the LLM can invoke to interact with the backend services.
"""

from langchain_core.tools import tool
from typing import Dict, Any, List

from app.core.database import SessionLocal
from app.services.portfolio_service import PortfolioService
from app.services.alert_service import AlertService
from app.services.event_service import EventService


@tool
def get_portfolio_summary(user_id: int) -> Dict[str, Any]:
    """Get the current summary of the user's portfolio, including holdings, total value, and P/L."""
    db = SessionLocal()
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio_summary(user_id=user_id)
        return portfolio.model_dump(mode="json")
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@tool
def get_recent_alerts(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Get the most recent active alerts for the user."""
    db = SessionLocal()
    try:
        service = AlertService(db)
        alerts = service.get_active_alerts(user_id=user_id, limit=limit)
        return [a.model_dump(mode="json") for a in alerts]
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        db.close()


@tool
def get_recent_news(limit: int = 6) -> List[Dict[str, Any]]:
    """Get recent market headlines and their analysis for a timely investor conversation."""
    db = SessionLocal()
    try:
        events = EventService(db).get_recent_news_events(limit=limit)
        return [event.model_dump(mode="json") for event in events]
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        db.close()


@tool
def acknowledge_alert(user_id: int, alert_id: str) -> Dict[str, Any]:
    """Acknowledge an alert to prevent further escalation."""
    db = SessionLocal()
    try:
        service = AlertService(db)
        alert = service.acknowledge_alert(user_id=user_id, alert_id=alert_id)
        if alert:
            return {"status": "success", "message": f"Alert {alert_id} acknowledged."}
        else:
            return {"status": "error", "message": "Alert not found or already acknowledged."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
