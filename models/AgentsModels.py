from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from services.db_config import Base
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

    session = relationship("Session", back_populates="agent")
    user = relationship("User", back_populates="agents")
