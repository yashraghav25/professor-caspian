"""
LangGraph Agent — PRD Sections 44-46.
Compiles the state machine for the autonomous agent.
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from typing import Dict, Any

from app.core.config import settings
from app.core.logging import get_logger
from app.agent.state import AgentState
from app.agent.tools import get_portfolio_summary, get_recent_alerts, acknowledge_alert

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
        
        self.system_prompt = """
        You are SentinelAI, an autonomous financial monitoring agent.
        You monitor the user's portfolio and manage market/news alerts.
        
        You have access to tools to check the portfolio, get alerts, and acknowledge them.
        When a user asks about their portfolio or an alert, use the tools to get the latest data.
        
        If the user wants to acknowledge an alert (e.g., they reply "ACK"), use the acknowledge_alert tool.
        Keep your responses concise, professional, and data-driven.
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
