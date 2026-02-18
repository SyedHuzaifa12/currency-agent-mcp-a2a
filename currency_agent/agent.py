"""Currency Agent with simple guardrails."""

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

# Import our simple guardrails
from currency_agent import guardrails

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are a currency conversion assistant. "
    "Follow these rules:\n"
    "1. ONLY answer currency-related questions\n"
    "2. ALWAYS use the get_exchange_rate tool - NEVER guess rates\n"
    "3. If asked non-currency questions, politely say you can only help with currency\n"
    "4. If you don't have data, say so - don't make up numbers\n"
    "\n"
    "Example:\n"
    "User: 'How much is 100 USD in EUR?'\n"
    "You: Use tool, then say 'Based on current rates, 100 USD is approximately 93 EUR'\n"
)


class GuardedAgent:
    """Simple guarded currency agent."""
    
    def __init__(self):
        self.agent = LlmAgent(
            model="gemini-2.5-flash",
            name="currency_agent",
            description="Currency conversion agent with safety guardrails",
            instruction=SYSTEM_INSTRUCTION,
            tools=[
                MCPToolset(
                    connection_params=StreamableHTTPConnectionParams(
                        url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
                    )
                )
            ],
        )
        logger.info("🛡️ Currency Agent with guardrails ready")
    
    def run(self, message: str) -> str:
        """
        Process message with guardrails.
        
        Args:
            message: User question
            
        Returns:
            str: Agent response
        """
        logger.info(f"📨 Got message: {message[:50]}...")
        
        # ========== CHECK INPUT ==========
        is_valid, error = guardrails.validate_input(message)
        if not is_valid:
            logger.warning(f"⚠️ Input blocked: {error}")
            return f"⚠️ {error}"
        
        # ========== CALL LLM ==========
        try:
            response = self.agent.run(message)
            logger.info(f"🤖 Got response: {response[:50]}...")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return "Sorry, I encountered an error. Please try again."
        
        # ========== CHECK OUTPUT ==========
        is_valid, error = guardrails.validate_output(response)
        if not is_valid:
            logger.error(f"❌ Output blocked: {error}")
            return "I generated an inappropriate response. Please rephrase your question."
        
        return response


# Create the agent for ADK web
_guarded = GuardedAgent()
root_agent = _guarded.agent