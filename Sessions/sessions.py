from fastapi import APIRouter, HTTPException, Depends, Request, staticfiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List
from schemas.UserSchemas import UserResponse
from schemas.SessionSchemas import SessionCreate, SessionUpdate, SessionResponse
from schemas.AgentSchemas import AgentResponse
from Services.db_config import get_db
from Services.session_management import create_session, get_active_sessions, update_session, invalidate_session, get_session_by_id
from Services.agent_management import get_agents_by_session
from sqlalchemy.orm import Session
from Services.auth import get_current_user
from models.SessionModels import Session as UserSession  # Correct import

session_routes = APIRouter(tags=["Sessions"])
session_routes.mount("/Static", staticfiles.StaticFiles(directory="Static"), name="Static")
templates = Jinja2Templates(directory="templates")

@session_routes.post("/sessions/create", response_model=SessionResponse)
async def create_user_session(session: SessionCreate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    new_session = create_session(current_user.id, session.name, db)
    return new_session

@session_routes.get("/sessions/user_sessions", response_model=List[SessionResponse])
async def get_user_sessions(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    sessions = get_active_sessions(current_user.id, db)
    return sessions

@session_routes.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_user_session(session_id: str, session: SessionUpdate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if db_session.user_id != current_user.id and not current_user.isadmin:
        raise HTTPException(status_code=403, detail="You do not have permission to update this session")
    updated_session = update_session(session_id, session.name, db)
    if not updated_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated_session

@session_routes.get("/sessions/{session_id}", response_class=HTMLResponse, name="session_details_page")
def session_details_page(request: Request, session_id: str, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    session = get_session_by_id(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    agents = get_agents_by_session(session_id, db)
    agent = agents[0] if agents else None
    return templates.TemplateResponse("session.html", {"request": request, "session": session, "current_user": current_user, "agent": agent})

@session_routes.delete("/sessions/{session_id}")
async def delete_user_session(session_id: str, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if db_session.user_id != current_user.id and not current_user.isadmin:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this session")
    success = invalidate_session(session_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session invalidated successfully"}
