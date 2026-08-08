"""
Market Data Provider Interface — PRD Section 21.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.event import EventBase


class MarketDataProvider(ABC):
    """Abstract interface for all market data providers (simulated or real)."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the provider (e.g. 'simulation', 'yahoo')."""
        pass
        
    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the current price for a symbol."""
        pass
        
    @abstractmethod
    async def fetch_recent_events(self) -> List[EventBase]:
        """Fetch recent market events."""
        pass
