from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SessionCreate(BaseModel):
    name: str

class SessionUpdate(BaseModel):
    name: Optional[str]

class SessionResponse(BaseModel):
    id: str
    name: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
