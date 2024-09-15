from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from schemas.AgentSchemas import AgentCreate, AgentUpdate, AgentResponse
from schemas.ChatSchemas import ChatCreate, ChatResponse
from Services.db_config import get_db
from Services.auth import get_current_user
from Services.agent_management import create_agent, get_agents_by_session, get_agent_by_id, update_agent, delete_agent, prepare_rag_chain, chains_cache
from Services.session_management import get_session_by_id
from models.UserModels import User
from models.ChatModels import Chat
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
async def prepare_agent(
    session_id: str,
    agent_id: str,
    instructions: str = Form(...),
    pdf_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Preparing agent {agent_id} for session {session_id}")
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to prepare this agent")
    
    document_path = None
    if pdf_file:
        # Save the uploaded PDF file
        file_location = f"documents/{pdf_file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await pdf_file.read())
        document_path = file_location

    try:
        # Call the function to prepare the RAG chain
        result = prepare_rag_chain(agent_id, instructions, [document_path] if document_path else [], db)
        
        if result.get("chain"):
            chains_cache[agent_id] = result["chain"]
            logger.info(f"RAG chain for agent {agent_id} has been cached")
            return {"message": "Agent prepared successfully"}
        else:
            logger.error(f"Failed to prepare RAG chain for agent {agent_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to prepare RAG chain")
    except Exception as e:
        logger.error(f"Error preparing agent: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@agent_routes.post("/sessions/{session_id}/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    session_id: str, 
    agent_id: str, 
    chat_data: ChatCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Chat request received for session {session_id}, agent {agent_id}")
    try:
        agent = get_agent_by_id(agent_id, db)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to chat with this agent")
        
        logger.info("Retrieving RAG chain from cache")
        chain = chains_cache.get(agent_id)
        if not chain:
            logger.warning(f"RAG chain not found in cache for agent {agent_id}. Attempting to recreate...")
            # Attempt to recreate the chain
            result = prepare_rag_chain(agent_id, agent.prompt_template, json.loads(agent.document_paths), db)
            chain = result.get("chain")
            if not chain:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to recreate RAG chain")
            chains_cache[agent_id] = chain
            logger.info(f"RAG chain recreated and cached for agent {agent_id}")
        
        logger.info("Generating response using RAG chain")
        response = chain.invoke(chat_data.message)
        logger.info(f"Raw response: {response}")
        
        answer = response['answer'] if isinstance(response, dict) and 'answer' in response else str(response)
        logger.info(f"Extracted answer: {answer}")
        
        logger.info("Saving chat interaction")
        new_chat = Chat(
            session_id=session_id,
            agent_id=agent_id,
            user_id=current_user.id,
            message=chat_data.message,
            response=answer,
            created_at=datetime.utcnow()
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        
        logger.info("Chat interaction saved successfully")
        return ChatResponse(
            id=str(new_chat.id),  # Ensure this is a string
            session_id=new_chat.session_id,
            agent_id=new_chat.agent_id,
            user_id=new_chat.user_id,
            message=new_chat.message,
            response=new_chat.response,
            created_at=new_chat.created_at
        )
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@agent_routes.get("/sessions/{session_id}/agents/{agent_id}/chat", response_class=HTMLResponse, name="chat_page")
async def chat_page(request: Request, session_id: str, agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return templates.TemplateResponse("chat.html", {"request": request, "session_id": session_id, "agent_id": agent_id, "current_user": current_user})
