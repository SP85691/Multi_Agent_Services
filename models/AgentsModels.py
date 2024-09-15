from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from Services.db_config import Base
from datetime import datetime
import uuid

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    document_paths = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=True)

    session = relationship("Session", back_populates="agent")
    user = relationship("User", back_populates="agents")
    chats = relationship("Chat", back_populates="agent")
