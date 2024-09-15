from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, staticfiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from schemas.UserSchemas import UserLogin, UserCreate, UserUpdate, UserResponse, UserRegisterResponse
from schemas.SessionSchemas import SessionCreate, SessionUpdate, SessionResponse
from Services.auth import create_access_token, get_current_user, create_user, authenticate_user, update_user, delete_user, get_user_by_username, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from Services.db_config import get_db
from Services.session_management import create_session, get_active_sessions, update_session, invalidate_session

user_routes = APIRouter(tags=['Users'])
templates = Jinja2Templates(directory="templates")
user_routes.mount("/Static", staticfiles.StaticFiles(directory="Static"), name="Static")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@user_routes.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@user_routes.post("/login", response_class=HTMLResponse, name="login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(username, password, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email or Password is Incorrect. Kindly try again or if you are a new user kindly signup yourself."})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.Username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/playground", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@user_routes.get("/signup", response_class=HTMLResponse, name="signup_page")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@user_routes.post("/signup", response_class=HTMLResponse, name="signup")
async def signup(request: Request, name: str = Form(...), username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if get_user_by_username(username, db):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "User already exists"})
    
    user_data = {
        "Name": name,
        "Username": username,
        "Email": email,
        "Password": password,
        "isadmin": False,
        "isactive": True
    }
    
    db_user = create_user(user_data, db)
    
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
    
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response

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
