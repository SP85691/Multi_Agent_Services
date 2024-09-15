from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from Services.db_config import Base
from datetime import datetime
import uuid

class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chats")
    agent = relationship("Agent", back_populates="chats")
    user = relationship("User", back_populates="chats")