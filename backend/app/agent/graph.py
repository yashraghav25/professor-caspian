"""
LangGraph Agent — PRD Sections 44-46.
Compiles the state machine for the autonomous agent.
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.agent.state import AgentState
from app.agent.tools import get_portfolio_summary, get_recent_alerts, acknowledge_alert
from app.caspian.client import get_caspian

logger = get_logger("agent_graph")


class SentinelAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.llm_model,
            temperature=0.2
        )
        
        self.tools = [get_portfolio_summary, get_recent_alerts, acknowledge_alert]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        caspian = get_caspian()
        channel_guide = caspian.behavior_prompt if caspian.is_ready else ""
        
        self.system_prompt = f"""
        You are SentinelAI, an autonomous portfolio risk agent for retail/pro investors.
        You monitor portfolios and communicate urgent alerts via Caspian (email + Telegram).

        IMPORTANT: Always use user_id=1 when calling tools (demo investor).

        When analysing an alert you MUST:
        1. Call get_portfolio_summary with user_id=1 so your advice reflects actual holdings and P/L.
        2. Explain WHAT happened in plain English (news + price action), not just scores.
        3. Explain WHY it matters for THIS portfolio (which positions, approx exposure/impact).
        4. Give 2-3 concrete suggested actions (e.g. trim size, hedge, wait for confirmation, set stop).

        Format your final answer as:
        **What happened**
        <2-4 sentences>

        **Portfolio impact**
        <1-3 sentences>

        **Suggested actions**
        1. ...
        2. ...
        3. ...

        Be concise, professional, and actionable. No fluff. No repeating the raw severity template.

        {channel_guide}
        """
        
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph state machine."""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("agent", self._run_agent)
        workflow.add_node("action", self._execute_tools)
        
        # Define edges
        workflow.set_entry_point("agent")
        
        # Conditional edge from agent to either action or END
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "action",
                "end": END
            }
        )
        
        # Edge from action back to agent
        workflow.add_edge("action", "agent")
        
        return workflow.compile()

    def _should_continue(self, state: AgentState) -> str:
        """Decide if we need to call tools or finish."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If there are tool calls, we continue to the action node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
            
        return "end"

    def _run_agent(self, state: AgentState) -> Dict[str, Any]:
        """Run the LLM."""
        messages = state.get("messages", [])
        
        # Prepend system prompt if it's not there
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + messages
            
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}

    def _execute_tools(self, state: AgentState) -> Dict[str, Any]:
        """Execute the tools requested by the LLM."""
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_responses = []
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Match tool
                tool_map = {t.name: t for t in self.tools}
                tool_func = tool_map.get(tool_name)
                
                if tool_func:
                    logger.info(f"Agent invoking tool: {tool_name}")
                    result = tool_func.invoke(tool_args)
                    
                    # Create ToolMessage (simulated as AIMessage with tool output for simplicity here, 
                    # in real LangGraph we'd use ToolMessage)
                    from langchain_core.messages import ToolMessage
                    tool_msg = ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=str(result),
                        name=tool_name
                    )
                    tool_responses.append(tool_msg)
                    
        return {"messages": tool_responses}

    async def run(self, user_id: int, user_message: str) -> str:
        """Entry point to run the agent with a user message."""
        
        state = {
            "messages": [HumanMessage(content=user_message)],
            "user_id": user_id,
            "portfolio_context": None,
            "recent_alerts": None,
            "action_taken": None
        }
        
        # Run graph
        result = await self.graph.ainvoke(state)
        
        # Extract final message
        final_message = result["messages"][-1].content
        return final_message

    async def compose_notification(
        self,
        summary: str,
        severity: str,
        channel: str,
        title: str = "",
    ) -> str:
        """Short, channel-aware alert text for Caspian delivery."""
        if channel == "telegram":
            rules = (
                "Max 240 characters. Plain text only, no markdown. "
                "Urgent tone. Include severity emoji (⚠️ or 🚨). "
                "One-line what happened + one action. End with 'Reply ACK'."
            )
        else:
            rules = (
                "Max 400 characters. Plain text, no markdown. "
                "Subject line feel. What happened + top action + 'Reply ACK to dismiss'."
            )

        prompt = f"""Write a {channel} alert notification for SentinelAI.

Severity: {severity}
Title: {title}
Rules: {rules}

Source analysis:
{summary[:1200]}

Output ONLY the notification text, nothing else."""
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        text = (response.content or "").strip()
        limit = 240 if channel == "telegram" else 400
        return text[:limit]

    async def compose_daily_report(
        self,
        portfolio_total: float,
        portfolio_pnl: float,
        portfolio_pnl_pct: float,
        holdings_summary: str,
        news_summary: str,
    ) -> str:
        """End-of-day email digest — crisp but informative."""
        prompt = f"""Write SentinelAI's end-of-day portfolio email digest.

Portfolio: ${portfolio_total:,.2f} total | P/L ${portfolio_pnl:+,.2f} ({portfolio_pnl_pct:+.2f}%)

Holdings:
{holdings_summary}

Today's news:
{news_summary}

Format (plain text, under 600 words):
1. Opening line with total value and day P/L
2. Holdings snapshot (2-3 bullet highlights)
3. News that could move positions tomorrow (2-3 bullets)
4. One-line outlook / watch item

Keep it crisp. No markdown headers. Investor-friendly tone."""
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return (response.content or "").strip()
