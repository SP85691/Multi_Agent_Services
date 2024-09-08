from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from schemas.UserSchemas import UserLogin, UserCreate, UserUpdate, UserResponse, UserRegisterResponse
from schemas.SessionSchemas import SessionCreate, SessionUpdate, SessionResponse
from services.auth import create_access_token, get_current_user, create_user, authenticate_user, update_user, delete_user, get_user_by_username, get_password_hash
from services.db_config import get_db
from services.session_management import create_session, get_active_sessions, update_session, invalidate_session

user_routes = APIRouter(prefix="/users", tags=['Users'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@user_routes.post("/login")
async def login_user_route(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(user.Username, user.Password, db)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": db_user.Username})
    return {"user": db_user, "access_token": access_token, "token_type": "bearer"}

@user_routes.post("/register", response_model=UserRegisterResponse)
async def register_user_route(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(user.Username, db):
        raise HTTPException(status_code=400, detail="User already exists")
    
    db_user = create_user(user.dict(by_alias=True), db)
    
    response_user = UserResponse(
        id=db_user.id,
        Name=db_user.Name,
        Username=db_user.Username,
        Email=db_user.Email,
        isadmin=db_user.isadmin,
        isactive=db_user.isactive,
        createdAt=db_user.createdAt,
        updatedAt=db_user.updatedAt
    )
    
    access_token = create_access_token(data={"sub": db_user.Username})
    return {"user": response_user, "access_token": access_token, "token_type": "bearer"}

@user_routes.put("/update_user/{user_id}", response_model=UserUpdate)
async def update_user_route(user_id: int, user: UserUpdate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not current_user.isadmin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to update this user")
    
    if user.Password:
        user.Password = get_password_hash(user.Password)
    
    db_user = update_user(user_id, user.dict(), db)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@user_routes.delete("/delete_user/{user_id}")
async def delete_user_route(user_id: int, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not current_user.isadmin:
        raise HTTPException(status_code=403, detail="You do not have permission to delete a user")
    result = delete_user(user_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result
