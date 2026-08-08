"""
Caspian Handlers — PRD Section 33.
Listens for inbound messages from Caspian (e.g. users replying 'ACK').
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.alert_service import AlertService
from app.models.user import User

logger = get_logger("caspian_handlers")
router = APIRouter()

@router.post("/caspian/webhook")
async def caspian_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint for Caspian to deliver inbound messages.
    PRD Section 42: Agent handles replies.
    """
    payload = await request.json()
    logger.info(f"Received Caspian webhook: {json.dumps(payload)}")
    
    # Extract message data
    # (Assuming Caspian standard webhook format)
    message_type = payload.get("type")
    
    if message_type == "message.created":
        data = payload.get("data", {})
        content = data.get("content", "").strip().lower()
        sender = data.get("from")
        
        if content in ["ack", "acknowledge"]:
            logger.info(f"Received ACK from {sender}")
            
            # Find user
            user = db.query(User).filter(User.email == sender).first()
            if user:
                # Acknowledge their most recent active alert
                alert_service = AlertService(db)
                active_alerts = alert_service.get_active_alerts(user.id, limit=1)
                
                if active_alerts:
                    alert_service.acknowledge_alert(user.id, active_alerts[0].alert_id)
                    logger.info(f"Acknowledged alert {active_alerts[0].alert_id} for user {user.email}")
                    
                    # Ideally we'd use Caspian to reply back saying "Alert acknowledged."
                
    return {"status": "ok"}
