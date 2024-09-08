from sqlalchemy.orm import Session
from models.SessionModels import Session as UserSession
from datetime import datetime
from typing import List
import uuid

def create_session(user_id: int, name: str, db: Session) -> UserSession:
    new_session = UserSession(id=str(uuid.uuid4()), name=name, user_id=user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_active_sessions(user_id: int, db: Session) -> List[UserSession]:
    return db.query(UserSession).filter(UserSession.user_id == user_id).all()

def get_session_by_id(session_id: str, db: Session) -> UserSession:
    return db.query(UserSession).filter(UserSession.id == session_id).first()

def update_session(session_id: str, name: str, db: Session) -> UserSession:
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.name = name
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session
    return None

def invalidate_session(session_id: str, db: Session) -> bool:
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return True
    return False