from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session as SessionDB
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from services.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from services.db_config import setup_db, get_db
from models.UserModels import User
from Users import user
from Sessions import sessions
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

# Set up CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
]

load_dotenv()

engine, Session = setup_db()

app = FastAPI(title="Multi Agent API Services", description="This is a multi agent api services")
app.include_router(user.user_routes)
app.include_router(sessions.session_routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/dashboard", response_class=HTMLResponse, name="read_root")
def read_root(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {"request": request, "current_user": current_user})

@app.get("/", response_class=HTMLResponse, name="read_root")
def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request}) 
                                                    
@app.get("/about", response_class=HTMLResponse, name="about_page")
def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/services", response_class=HTMLResponse, name="services_page")
def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse, name="contact_page")
def contact_page(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionDB = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.Username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/logout", response_class=HTMLResponse, name="logout")
def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
