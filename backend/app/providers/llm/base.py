"""
LLM Provider Abstraction — PRD Section 21.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def analyze_news(self, headline: str, summary: str) -> Dict[str, Any]:
        """
        Analyze a news event and return structured output.
        Must conform to NewsAnalysisSchema.
        """
        pass
        
    @abstractmethod
    async def invoke_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the agentic workflow with the given state.
        """
        pass
