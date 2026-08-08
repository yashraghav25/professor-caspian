"""
News Provider Interface — PRD Section 21.
"""

from abc import ABC, abstractmethod
from typing import List

from app.schemas.event import EventBase


class NewsProvider(ABC):
    """Abstract interface for all news providers (simulated or real)."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the provider (e.g. 'simulation', 'finnhub')."""
        pass
        
    @abstractmethod
    async def fetch_recent_news(self) -> List[EventBase]:
        """Fetch recent news events."""
        pass
