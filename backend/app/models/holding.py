"""Holding model — PRD Section 35."""

from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    average_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

    @property
    def position_value(self) -> float:
        """Current position value = quantity × current_price."""
        price = self.current_price if self.current_price else self.average_price
        return self.quantity * price

    @property
    def cost_basis(self) -> float:
        """Original cost = quantity × average_price."""
        return self.quantity * self.average_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P/L = position_value - cost_basis."""
        return self.position_value - self.cost_basis
