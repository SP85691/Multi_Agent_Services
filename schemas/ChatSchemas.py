from pydantic import BaseModel
from datetime import datetime

class ChatBase(BaseModel):
    message: str

class ChatCreate(BaseModel):
    message: str

class ChatResponse(BaseModel):
    id: str
    session_id: str
    agent_id: str
    user_id: int
    message: str
    response: str
    created_at: datetime

    class Config:
        orm_mode = True