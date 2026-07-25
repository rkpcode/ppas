from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from app.models.staff import Staff
from app.services.auth_service import get_current_user
from app.agents.inventory_agent.graph import run_inventory_agent

router = APIRouter(prefix="/agents/inventory", tags=["Agents"])

class AgentQuery(BaseModel):
    message: str

class AgentResponse(BaseModel):
    response: str

@router.post("/query", response_model=AgentResponse)
def inventory_query(
    query: AgentQuery,
    current_user: Annotated[Staff, Depends(get_current_user)]
):
    try:
        response_text = run_inventory_agent(query.message)
        return AgentResponse(response=response_text)
    except Exception as e:
        # Catch LLM or tool execution errors
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
