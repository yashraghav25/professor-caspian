"""
Background Polling Worker
Continuously polls Finnhub for live market prices and news for user holdings.
"""
import asyncio
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.market_data_service import MarketDataService

logger = get_logger("polling_worker")

# Global flags
_polling_active = False
_polling_task = None
# Allow simulation to pause polling during a fake crash
_demo_crash_active = False 

async def start_polling():
    global _polling_active, _polling_task
    if _polling_active:
        return
        
    _polling_active = True
    _polling_task = asyncio.create_task(_poll_loop())
    logger.info("Live market data polling started.")

async def stop_polling():
    global _polling_active, _polling_task
    _polling_active = False
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
    logger.info("Live market data polling stopped.")

def pause_for_demo(duration_seconds: int = 30):
    """Temporarily pauses polling so the demo crash prices aren't immediately overwritten."""
    global _demo_crash_active
    _demo_crash_active = True
    logger.info(f"Polling paused for {duration_seconds}s demo crash...")
    
    async def _unpause():
        await asyncio.sleep(duration_seconds)
        global _demo_crash_active
        _demo_crash_active = False
        logger.info("Demo crash finished. Polling resumed.")
        
    asyncio.create_task(_unpause())

async def _poll_loop():
    """Main loop for polling Finnhub."""
    # Start with a quick delay to let the app start up
    await asyncio.sleep(5)
    
    while _polling_active:
        if not _demo_crash_active:
            db: Session = SessionLocal()
            try:
                service = MarketDataService(db)
                
                # 1. Update prices (Fast)
                service.update_portfolio_live_prices()
                
                # 2. Fetch news (Slightly slower, don't need it every 10 seconds)
                # We'll fetch news once a minute (roughly every 6 price iterations)
                if getattr(_poll_loop, "iteration", 0) % 6 == 0:
                    service.fetch_latest_news()
                    
                _poll_loop.iteration = getattr(_poll_loop, "iteration", 0) + 1
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
            finally:
                db.close()
                
        # Wait 10 seconds before next poll
        await asyncio.sleep(10)
