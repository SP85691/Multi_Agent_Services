from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, staticfiles
from sqlalchemy.orm import Session as SessionDB
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from Services.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, get_optional_user
from Services.db_config import setup_db, get_db
from models.UserModels import User
from Users import user
from Sessions import sessions
from Agents import agents
from Services.session_management import get_active_sessions, get_session_by_id
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

# Set up CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    # Add other origins as needed
]

load_dotenv()

engine, Session = setup_db()

app = FastAPI(title="Multi Agent API Services", description="This is a multi agent api services")
app.include_router(user.user_routes)
app.include_router(sessions.session_routes)
app.include_router(agents.agent_routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/Static", staticfiles.StaticFiles(directory="Static"), name="Static")
templates = Jinja2Templates(directory="templates")

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/dashboard", response_class=HTMLResponse, name="dashboard_page")
async def dashboard_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {"request": request, "current_user": current_user})

@app.get("/", response_class=HTMLResponse, name="read_root")
async def read_root(request: Request, current_user: User = Depends(get_optional_user)):
    return templates.TemplateResponse("home.html", {"request": request, "current_user": current_user})

@app.get("/about", response_class=HTMLResponse, name="about_page")
async def about_page(request: Request, current_user: User = Depends(get_optional_user)):
    return templates.TemplateResponse("about.html", {"request": request, "current_user": current_user})

@app.get("/services", response_class=HTMLResponse, name="services_page")
async def services_page(request: Request, current_user: User = Depends(get_optional_user)):
    return templates.TemplateResponse("services.html", {"request": request, "current_user": current_user})

@app.get("/contact", response_class=HTMLResponse, name="contact_page")
async def contact_page(request: Request, current_user: User = Depends(get_optional_user)):
    return templates.TemplateResponse("contact.html", {"request": request, "current_user": current_user})

@app.get("/playground", response_class=HTMLResponse, name="playground_page")
async def playground_page(request: Request, current_user: User = Depends(get_current_user), db: SessionDB = Depends(get_db)):
    sessions = get_active_sessions(current_user.id, db)
    return templates.TemplateResponse("playground.html", {"request": request, "current_user": current_user, "sessions": sessions})

@app.get("/logout", response_class=HTMLResponse, name="logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/404", response_class=HTMLResponse, name="not_found_page")
async def not_found_page(request: Request, current_user: User = Depends(get_optional_user)):
    return templates.TemplateResponse("404.html", {"request": request, "current_user": current_user})

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/404")
