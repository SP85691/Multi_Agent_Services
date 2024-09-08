from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatBase(BaseModel):
    message: str

class ChatCreate(ChatBase):
    session_id: str
    agent_id: str
    user_id: int

class ChatResponse(ChatBase):
    id: str
    session_id: str
    agent_id: str
    user_id: int
    response: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True