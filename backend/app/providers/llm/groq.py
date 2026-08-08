"""
Groq LLM Provider Implementation — PRD Section 11, 72.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from typing import Dict, Any

from app.core.config import settings
from app.providers.llm.base import LLMProvider
from app.schemas.event import NewsAnalysisSchema
from app.core.logging import get_logger

logger = get_logger("groq_provider")


class GroqProvider(LLMProvider):
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.llm_model,
            temperature=0.1  # Low temperature for analytical tasks
        )
        
    async def analyze_news(self, headline: str, summary: str) -> Dict[str, Any]:
        """
        Use Groq to analyze news for structured entities, sentiment, and impact.
        PRD Section 28 & 72.
        """
        parser = JsonOutputParser(pydantic_object=NewsAnalysisSchema)
        
        prompt = PromptTemplate(
            template="""
            Analyze the following news event for its impact on financial markets.
            Identify any specific companies (entities) or sectors mentioned.
            Determine the sentiment (positive, neutral, negative) and the potential impact (low, medium, high).
            Provide a short reason for your analysis and your confidence level (0.0 to 1.0).
            
            Headline: {headline}
            Summary: {summary}
            
            {format_instructions}
            """,
            input_variables=["headline", "summary"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt | self.llm | parser
        
        logger.info(f"Analyzing news via Groq: {headline[:30]}...")
        
        try:
            result = await chain.ainvoke({"headline": headline, "summary": summary or ""})
            return result
        except Exception as e:
            logger.error(f"Failed to analyze news with Groq: {e}")
            # Fallback
            return {
                "entities": [],
                "sectors": [],
                "sentiment": "neutral",
                "impact": "low",
                "confidence": 0.0,
                "reason": "Analysis failed."
            }

    async def invoke_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Agent logic is handled via LangGraph in app.agent
        pass
