"""
Market Data Service — PRD Sections 35, 50.
Fetches historical cost basis (yfinance) and live market prices & news (Finnhub).
"""

import os
import requests
import yfinance as yf
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.holding import Holding
from app.models.portfolio import Portfolio
from app.models.event import MarketEvent, NewsEvent
from app.services.event_service import EventService
from app.core.config import settings

logger = get_logger("market_data")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

class MarketDataService:
    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)

    def get_historical_closing_price(self, symbol: str, date: datetime) -> float:
        """Fetch the closing price of a stock on or just before a specific date using yfinance."""
        try:
            # We fetch a 5-day window ending on the target date to ensure we hit a trading day
            end_date_str = date.strftime('%Y-%m-%d')
            start_date_str = (date - timedelta(days=5)).strftime('%Y-%m-%d')
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date_str, end=end_date_str)
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol} on {date}. Using fallback $100.")
                return 100.0
                
            # Return the last available closing price in that window
            return float(hist.iloc[-1]['Close'])
        except Exception as e:
            logger.error(f"Error fetching historical price for {symbol}: {e}")
            return 100.0

    def get_live_price(self, symbol: str) -> float:
        """Fetch current live price from Finnhub."""
        if not FINNHUB_API_KEY:
            logger.error("FINNHUB_API_KEY is not set.")
            return 0.0
            
        try:
            url = f"{FINNHUB_BASE_URL}/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return float(data.get("c", 0.0)) # 'c' is current price
        except Exception as e:
            logger.error(f"Error fetching live price for {symbol}: {e}")
            return 0.0

    def update_portfolio_live_prices(self):
        """Poll Finnhub for all active holdings and update their current_price."""
        holdings = self.db.query(Holding).all()
        if not holdings:
            return
            
        symbols = set(h.symbol for h in holdings if h.symbol.upper() != "CASH")
        
        for symbol in symbols:
            live_price = self.get_live_price(symbol)
            if live_price > 0:
                # Update all holdings with this symbol
                symbol_holdings = [h for h in holdings if h.symbol == symbol]
                for h in symbol_holdings:
                    # Optional: generate a MarketEvent if price changed significantly? 
                    # For now, just update the price so the UI P/L is live.
                    h.current_price = live_price
                    logger.debug(f"Live updated {symbol} to ${live_price:.2f}")
                    
        self.db.commit()

    def fetch_latest_news(self):
        """Poll Finnhub for recent news related to active holdings."""
        if not FINNHUB_API_KEY:
            return
            
        holdings = self.db.query(Holding).all()
        if not holdings:
            return
            
        symbols = set(h.symbol for h in holdings if h.symbol.upper() != "CASH")
        
        # Calculate date range (last 3 days)
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        for symbol in symbols:
            try:
                url = f"{FINNHUB_BASE_URL}/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                news_items = response.json()
                
                # Process the top 2 recent news items per symbol
                for item in news_items[:2]:
                    # Create a NewsEvent payload
                    # Note: Finnhub item['id'] can be used to prevent duplicates, but EventService 
                    # has logic to generate unique event_ids. We'll use the external ID if possible.
                    
                    event_id = f"NEWS_{item.get('id', self.event_service.generate_event_id())}"
                    
                    # Check if already processed
                    existing = self.db.query(NewsEvent).filter(NewsEvent.event_id == event_id).first()
                    if not existing:
                        from app.schemas.event import EventBase
                        event = EventBase(
                            event_id=event_id,
                            event_type="NEWS",
                            source="finnhub",
                            symbol=symbol,
                            payload={
                                "headline": item.get("headline", ""),
                                "summary": item.get("summary", ""),
                                "source_name": item.get("source", "Finnhub"),
                                "url": item.get("url", ""),
                            },
                            occurred_at=datetime.fromtimestamp(item.get("datetime", int(datetime.now().timestamp())), tz=timezone.utc)
                        )
                        self.event_service.ingest_event(event)
                        logger.info(f"Ingested new news for {symbol}: {item.get('headline')}")
                        
            except Exception as e:
                logger.error(f"Error fetching news for {symbol}: {e}")
