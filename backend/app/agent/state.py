"""
LangGraph Agent State — PRD Sections 44, 46.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    The state for the LangGraph agent.
    Maintains the conversation history and context about the user's portfolio/alerts.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: int
    portfolio_context: Optional[Dict[str, Any]]
    recent_alerts: Optional[List[Dict[str, Any]]]
    action_taken: Optional[str]
