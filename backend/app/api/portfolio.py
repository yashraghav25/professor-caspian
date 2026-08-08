"""
Portfolio API endpoints — PRD Section 36.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.portfolio import PortfolioResponse, HoldingCreate, HoldingUpdate
from app.services.portfolio_service import PortfolioService

router = APIRouter()

# For hackathon MVP, we'll hardcode the user_id to 1 (the demo user created in main.py)
DEMO_USER_ID = 1

@router.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio(db: Session = Depends(get_db)):
    """Return the user's main portfolio summary with calculated weights and PNL."""
    service = PortfolioService(db)
    return service.get_portfolio_summary(user_id=DEMO_USER_ID)

@router.post("/portfolio/holdings")
def add_holding(holding: HoldingCreate, db: Session = Depends(get_db)):
    """Add a holding to the default portfolio."""
    service = PortfolioService(db)
    # Get the default portfolio ID for the user
    portfolio = service.get_portfolio(user_id=DEMO_USER_ID)
    return service.add_holding(user_id=DEMO_USER_ID, portfolio_id=portfolio.id, holding_in=holding)

@router.delete("/portfolio/holdings/{holding_id}")
def remove_holding(holding_id: int, db: Session = Depends(get_db)):
    """Remove a holding from the default portfolio."""
    service = PortfolioService(db)
    portfolio = service.get_portfolio(user_id=DEMO_USER_ID)
    service.remove_holding(user_id=DEMO_USER_ID, portfolio_id=portfolio.id, holding_id=holding_id)
    return {"success": True}
