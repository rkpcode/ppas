from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from app.agents.inventory_agent.tools import (
    search_medicine, check_stock, check_expiry, check_low_stock
)
from app.agents.inventory_agent.prompts import INVENTORY_AGENT_SYSTEM_PROMPT
from app.config import settings

def run_inventory_agent(user_message: str) -> str:
    """
    Executes the inventory agent graph given a user message.
    Uses NVIDIA NIM API (OpenAI-compatible endpoint).
    """
    llm = ChatOpenAI(
        model=settings.NVIDIA_AGENT_MODEL,
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=settings.NVIDIA_API_KEY,
        temperature=0
    )
    
    tools = [search_medicine, check_stock, check_expiry, check_low_stock]
    
    agent_executor = create_react_agent(llm, tools, state_modifier=INVENTORY_AGENT_SYSTEM_PROMPT)
    
    # Run the graph
    result = agent_executor.invoke({"messages": [("user", user_message)]})
    
    # Return the final message content
    return result["messages"][-1].content
