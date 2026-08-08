"""
Alert API endpoints — PRD Section 36.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.alert_service import AlertService
from app.schemas.alert import AlertResponse, AcknowledgeRequest

router = APIRouter()

# Demo user
DEMO_USER_ID = 1

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(limit: int = 10, db: Session = Depends(get_db)):
    """Active and recent alerts."""
    service = AlertService(db)
    return service.get_active_alerts(user_id=DEMO_USER_ID, limit=limit)


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Alert details."""
    service = AlertService(db)
    alert = service.get_alert(user_id=DEMO_USER_ID, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: str, req: AcknowledgeRequest, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    service = AlertService(db)
    alert = service.acknowledge_alert(user_id=DEMO_USER_ID, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return service.get_alert(user_id=DEMO_USER_ID, alert_id=alert_id)
