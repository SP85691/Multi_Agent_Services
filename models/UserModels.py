from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from services.db_config import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Username = Column(String, unique=True)
    Email = Column(String, unique=True, index=True)
    Password = Column(String)
    isadmin = Column(Boolean, default=False)
    isactive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
