"""
Caspian Client integration — PRD Sections 33, 40-42.
Handles sending outbound notifications via Caspian SDK.
"""

from caspian import Caspian
import asyncio

from app.core.config import settings
from app.core.logging import get_logger
from app.models.notification import Notification, NotificationStatus
from app.services.notification_service import NotificationService
from app.core.database import SessionLocal

logger = get_logger("caspian_client")

# Initialize Caspian client globally
caspian_client = Caspian(
    api_key=settings.caspian_api_key, 
    base_url=settings.caspian_base_url
)


async def send_notification_via_caspian(notification_id: int):
    """
    Sends a pending notification via Caspian SDK.
    Looks up the alert details and builds a rich message.
    """
    db = SessionLocal()
    try:
        service = NotificationService(db)
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif or notif.status != NotificationStatus.PENDING:
            return
            
        alert = notif.alert
        user = alert.user
        
        # In a real app we'd map internal channel to Caspian provider
        # For this hackathon, we assume the user's primary email/telegram are setup in Caspian's channel config
        
        # Build the message
        severity_icon = "🔴" if alert.severity_level == "CRITICAL" else "🟠" if alert.severity_level == "HIGH" else "🟡"
        
        message_body = (
            f"{severity_icon} **SentinelAI {alert.severity_level} ALERT**\n\n"
            f"**{alert.title}**\n\n"
            f"Score: {alert.severity_score:.1f}/100\n"
            f"Reason: {alert.reason}\n\n"
            f"Reply 'ACK' to acknowledge this alert and pause escalations."
        )
        
        logger.info(f"Sending via Caspian ({notif.channel}) to user {user.email}")
        
        try:
            # We'll use Caspian to send the message.
            # Assuming we find a channel or pass user ID to Caspian
            # This requires Caspian channels to be configured
            
            response = await asyncio.to_thread(
                caspian_client.messages.create,
                to=user.email, # Or a channel ID if mapped
                content=message_body
            )
            
            logger.info(f"Caspian send success. Message ID: {response.id}")
            service.update_notification_status(
                notif.id, 
                NotificationStatus.SENT, 
                message_id=response.id
            )
            
        except Exception as e:
            logger.error(f"Caspian send failed: {e}")
            service.update_notification_status(
                notif.id, 
                NotificationStatus.FAILED, 
                error=str(e)
            )
            
    finally:
        db.close()
