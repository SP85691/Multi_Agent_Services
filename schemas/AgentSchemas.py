from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AgentBase(BaseModel):
    name: str

class AgentCreate(AgentBase):
    session_id: str
    user_id: int

class AgentUpdate(AgentBase):
    pass

class AgentResponse(AgentBase):
    id: str
    session_id: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
