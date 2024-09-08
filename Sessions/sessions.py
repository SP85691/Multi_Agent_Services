from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List
from schemas.UserSchemas import UserResponse
from schemas.SessionSchemas import SessionCreate, SessionUpdate, SessionResponse
from services.db_config import get_db
from services.session_management import create_session, get_active_sessions, update_session, invalidate_session, get_session_by_id
from sqlalchemy.orm import Session
from services.auth import get_current_user
from models.SessionModels import Session as UserSession  # Correct import

session_routes = APIRouter(prefix="/sessions", tags=["Sessions"])
templates = Jinja2Templates(directory="templates")

@session_routes.post("/create", response_model=SessionResponse)
async def create_user_session(session: SessionCreate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    new_session = create_session(current_user.id, session.name, db)
    return new_session

@session_routes.get("/user_sessions", response_model=List[SessionResponse])
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

@session_routes.get("/playground/{session_id}", response_class=HTMLResponse, name="session_details_page")
def session_details_page(request: Request, session_id: str, db: Session = Depends(get_db)):
    session = get_session_by_id(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return templates.TemplateResponse("session.html", {"request": request, "session": session})

@session_routes.delete("/sessions/{session_id}")
async def delete_user_session(session_id: str, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if db_session.user_id != current_user.id and not current_user.isadmin:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this session")
    success = invalidate_session(session_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session invalidated successfully"}
