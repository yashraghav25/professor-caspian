"""
Portfolio Service — PRD Section 50, 27.
Handles calculating portfolio value, weights, exposure, and portfolio impact.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.schemas.portfolio import PortfolioCreate, HoldingCreate, HoldingUpdate, PortfolioResponse, HoldingResponse


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def get_portfolio(self, user_id: int, portfolio_id: int = None) -> Portfolio:
        """Get the user's primary portfolio if portfolio_id is not provided."""
        query = self.db.query(Portfolio).filter(Portfolio.user_id == user_id)
        if portfolio_id:
            query = query.filter(Portfolio.id == portfolio_id)
        
        portfolio = query.first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return portfolio

    def get_portfolio_summary(self, user_id: int, portfolio_id: int = None) -> PortfolioResponse:
        """Get portfolio with calculated values, weights, and PNL."""
        portfolio = self.get_portfolio(user_id, portfolio_id)
        holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()

        total_value = sum(h.position_value for h in holdings)
        invested_value = sum(h.cost_basis for h in holdings)
        
        # Calculate cash holding if it exists
        cash_holding = next((h for h in holdings if h.symbol.upper() == "CASH"), None)
        cash_value = cash_holding.position_value if cash_holding else 0.0

        total_pnl = total_value - invested_value
        total_pnl_percent = (total_pnl / invested_value * 100) if invested_value > 0 else 0.0

        # Create rich holding responses with calculated weights
        holding_responses = []
        for h in holdings:
            weight = (h.position_value / total_value * 100) if total_value > 0 else 0.0
            
            # Use current_price to calculate change_percent, or 0 if not set
            current_price = h.current_price if h.current_price else h.average_price
            change_percent = ((current_price - h.average_price) / h.average_price * 100) if h.average_price > 0 else 0.0

            holding_responses.append(HoldingResponse(
                id=h.id,
                symbol=h.symbol,
                quantity=h.quantity,
                average_price=h.average_price,
                current_price=h.current_price,
                position_value=h.position_value,
                weight=weight,
                unrealized_pnl=h.unrealized_pnl,
                change_percent=change_percent
            ))

        return PortfolioResponse(
            id=portfolio.id,
            name=portfolio.name,
            base_currency=portfolio.base_currency,
            total_value=total_value,
            invested_value=invested_value,
            cash_value=cash_value,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            holdings=holding_responses,
            created_at=portfolio.created_at
        )

    def add_holding(self, user_id: int, portfolio_id: int, holding_in: HoldingCreate) -> Holding:
        portfolio = self.get_portfolio(user_id, portfolio_id)
        
        # Check if holding already exists
        existing = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.symbol == holding_in.symbol.upper()
        ).first()

        if existing:
            # Simple average cost calculation
            total_cost = (existing.quantity * existing.average_price) + (holding_in.quantity * holding_in.average_price)
            new_quantity = existing.quantity + holding_in.quantity
            existing.average_price = total_cost / new_quantity if new_quantity > 0 else 0
            existing.quantity = new_quantity
            if holding_in.current_price is not None:
                existing.current_price = holding_in.current_price
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            new_holding = Holding(
                portfolio_id=portfolio.id,
                symbol=holding_in.symbol.upper(),
                quantity=holding_in.quantity,
                average_price=holding_in.average_price,
                current_price=holding_in.current_price or holding_in.average_price
            )
            self.db.add(new_holding)
            self.db.commit()
            self.db.refresh(new_holding)
            return new_holding

    def update_holding(self, user_id: int, portfolio_id: int, holding_id: int, holding_in: HoldingUpdate) -> Holding:
        portfolio = self.get_portfolio(user_id, portfolio_id)
        holding = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.id == holding_id
        ).first()

        if not holding:
            raise HTTPException(status_code=404, detail="Holding not found")

        if holding_in.quantity is not None:
            holding.quantity = holding_in.quantity
        if holding_in.average_price is not None:
            holding.average_price = holding_in.average_price
        if holding_in.current_price is not None:
            holding.current_price = holding_in.current_price

        self.db.commit()
        self.db.refresh(holding)
        return holding

    def remove_holding(self, user_id: int, portfolio_id: int, holding_id: int):
        portfolio = self.get_portfolio(user_id, portfolio_id)
        holding = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.id == holding_id
        ).first()

        if not holding:
            raise HTTPException(status_code=404, detail="Holding not found")
            
        self.db.delete(holding)
        self.db.commit()
        
    def get_portfolio_weight(self, user_id: int, symbol: str) -> float:
        """Helper for impact engine: returns the portfolio weight (0.0 to 1.0) of a symbol."""
        portfolio = self.get_portfolio(user_id) # Uses default portfolio
        holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        
        total_value = sum(h.position_value for h in holdings)
        if total_value == 0:
            return 0.0
            
        target_holding = next((h for h in holdings if h.symbol.upper() == symbol.upper()), None)
        if not target_holding:
            return 0.0
            
        return target_holding.position_value / total_value
