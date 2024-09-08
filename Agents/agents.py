from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from schemas.AgentSchemas import AgentCreate, AgentUpdate, AgentResponse
from services.db_config import get_db
from services.auth import get_current_user
from services.agent_management import create_agent, get_agents_by_session, get_agent_by_id, update_agent, delete_agent
from services.session_management import get_session_by_id
from models.UserModels import User
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

agent_routes = APIRouter(tags=["Agents"])
templates = Jinja2Templates(directory="templates")

@agent_routes.post("/sessions/{session_id}/agents", response_model=AgentResponse)
async def create_new_agent(session_id: str, agent_data: AgentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != agent_data.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to create an agent for this user")
    new_agent = create_agent(agent_data, db)
    return new_agent

@agent_routes.get("/sessions/{session_id}/agents", response_model=List[AgentResponse])
async def get_agents_for_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agents = get_agents_by_session(session_id, db)
    return agents

@agent_routes.get("/sessions/{session_id}/agents/{agent_id}", response_class=HTMLResponse, name="agent_details_page")
async def get_agent_details(request: Request, session_id: str, agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    session = get_session_by_id(session_id, db)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return templates.TemplateResponse("agent.html", {"request": request, "session": session, "agent": agent, "current_user": current_user})

@agent_routes.put("/sessions/{session_id}/agents/{agent_id}", response_model=AgentResponse)
async def update_existing_agent(session_id: str, agent_id: str, agent_data: AgentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this agent")
    updated_agent = update_agent(agent_id, agent_data, db)
    return updated_agent

@agent_routes.delete("/sessions/{session_id}/agents/{agent_id}")
async def delete_existing_agent(session_id: str, agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this agent")
    success = delete_agent(agent_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete agent")
    return {"message": "Agent deleted successfully"}

@agent_routes.post("/sessions/{session_id}/agents/{agent_id}/prepare")
async def prepare_agent(session_id: str, agent_id: str, instructions: str = Form(...), documents: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to prepare this agent")
    
    # Process the uploaded documents and instructions here
    # For example, save the documents to a directory and store the instructions in the database

    return {"message": "Agent prepared successfully"}
