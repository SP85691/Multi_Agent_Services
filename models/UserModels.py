from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from services.db_config import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String, nullable=False)
    Username = Column(String, unique=True, index=True, nullable=False)
    Email = Column(String, unique=True, index=True, nullable=False)
    Password = Column(String, nullable=False)
    isadmin = Column(Boolean, default=False)
    isactive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("Session", back_populates="user")
    agents = relationship("Agent", back_populates="user")
    chats = relationship("Chat", back_populates="user")  # Add this line
