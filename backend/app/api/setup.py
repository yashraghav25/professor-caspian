"""
Setup API endpoints for initializing the portfolio with historical data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.services.market_data_service import MarketDataService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("setup_api")

class SetupRequest(BaseModel):
    symbols: List[str]
    timeframe: str  # "1_month", "6_months", "1_year"

DEMO_USER_ID = 1


def _clear_user_portfolio(db: Session) -> None:
    """Remove portfolio + dependent rows (holdings, alerts, notifications)."""
    from app.models.alert import Alert
    from app.models.notification import Notification

    existing_portfolio = db.query(Portfolio).filter(Portfolio.user_id == DEMO_USER_ID).first()
    if not existing_portfolio:
        return

    alert_ids = [
        a.alert_id
        for a in db.query(Alert).filter(Alert.portfolio_id == existing_portfolio.id).all()
    ]
    if alert_ids:
        db.query(Notification).filter(Notification.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        db.query(Alert).filter(Alert.portfolio_id == existing_portfolio.id).delete(synchronize_session=False)

    db.query(Holding).filter(Holding.portfolio_id == existing_portfolio.id).delete(synchronize_session=False)
    db.delete(existing_portfolio)
    db.commit()


def _get_historical_date(timeframe: str) -> datetime:
    now = datetime.now(timezone.utc)
    if timeframe == "1_month":
        return now - relativedelta(months=1)
    elif timeframe == "6_months":
        return now - relativedelta(months=6)
    elif timeframe == "1_year":
        return now - relativedelta(years=1)
    return now - relativedelta(months=6) # default

@router.post("/setup/portfolio")
def initialize_portfolio(request: SetupRequest, db: Session = Depends(get_db)):
    """Initialize a portfolio with historical prices."""
    if len(request.symbols) == 0:
        raise HTTPException(status_code=400, detail="Must select at least 1 stock.")

    # 1. Clear existing portfolio/holdings (and dependent alerts)
    _clear_user_portfolio(db)

    # 2. Create new portfolio
    portfolio = Portfolio(user_id=DEMO_USER_ID, name="Main Portfolio", base_currency="USD")
    db.add(portfolio)
    db.flush()

    # 3. Calculate historical date
    target_date = _get_historical_date(request.timeframe)
    logger.info(f"Initializing portfolio for {request.symbols} on {target_date.date()}")

    # 4. Fetch historical prices and add holdings
    # We'll allocate an equal amount of "shares" roughly to total $100k
    # Fake a $100k portfolio split evenly
    allocation_per_stock = 100000.0 / len(request.symbols)
    
    market_service = MarketDataService(db)
    
    for symbol in request.symbols:
        symbol = symbol.upper()
        # Fetch historical cost basis
        historical_price = market_service.get_historical_closing_price(symbol, target_date)
        
        # Calculate quantity to match allocation
        quantity = int(allocation_per_stock / historical_price) if historical_price > 0 else 0
        
        # Current price will be updated by polling, but start it with historical
        holding = Holding(
            portfolio_id=portfolio.id,
            symbol=symbol,
            quantity=float(quantity),
            average_price=historical_price,
            current_price=historical_price
        )
        db.add(holding)

    db.commit()
    
    # 5. Kickoff a quick live price update synchronously so the UI has immediate live data
    market_service.update_portfolio_live_prices()
    
    return {"status": "success", "message": f"Portfolio initialized with {len(request.symbols)} stocks from {request.timeframe} ago."}


@router.delete("/setup/portfolio")
def reset_portfolio(db: Session = Depends(get_db)):
    """Clear the portfolio so the onboarding modal can run again."""
    _clear_user_portfolio(db)
    return {"status": "success", "message": "Portfolio cleared."}
