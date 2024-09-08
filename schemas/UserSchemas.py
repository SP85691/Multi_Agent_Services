from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    Name: str
    Username: str
    Email: str
    Password: str
    isadmin: Optional[bool] = False
    isactive: Optional[bool] = True

class UserUpdate(BaseModel):
    Name: Optional[str]
    Username: Optional[str]
    Email: Optional[str]
    Password: Optional[str]
    isadmin: Optional[bool]
    isactive: Optional[bool]

class UserLogin(BaseModel):
    Username: str
    Password: str
    
class UserResponse(BaseModel):
    id: int
    Name: str
    Username: str
    Email: str
    isadmin: bool
    isactive: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class UserRegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str

class UserSession(BaseModel):
    id: str
    name: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
