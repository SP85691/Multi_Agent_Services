from pydantic import BaseModel
from typing import Optional, List
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
    document_paths: Optional[List[str]] = None
    prompt_template: Optional[str] = None

    class Config:
        orm_mode = True

# Remove the AgentPrepare class