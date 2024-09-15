from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from schemas.ChatSchemas import ChatCreate, ChatResponse
from Services.db_config import get_db
from Services.auth import get_current_user
from Services.agent_management import get_agent_by_id, chains_cache
from models.UserModels import User
from models.ChatModels import Chat
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
import json

chat_routes = APIRouter(tags=["Chat"])
templates = Jinja2Templates(directory="templates")

@chat_routes.post("/sessions/{session_id}/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(session_id: str, agent_id: str, chat_data: ChatCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to chat with this agent")
    
    # Retrieve the RAG chain from the cache
    chain = chains_cache.get(agent_id)
    if not chain:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="RAG chain not found for this agent")
    
    # Generate the response using the RAG chain
    response = chain.invoke(chat_data.message)
    
    # Save the chat interaction
    new_chat = Chat(
        session_id=session_id,
        agent_id=agent_id,
        user_id=current_user.id,
        message=chat_data.message,
        response=response.content,
        created_at=datetime.utcnow()
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    return new_chat

@chat_routes.get("/sessions/{session_id}/agents/{agent_id}/chat", response_class=HTMLResponse, name="chat_page")
async def chat_page(request: Request, session_id: str, agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return templates.TemplateResponse("chat.html", {"request": request, "session_id": session_id, "agent_id": agent_id, "current_user": current_user})