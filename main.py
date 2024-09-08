from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session as SessionDB
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from services.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from services.db_config import setup_db, get_db
from models.UserModels import User
from Users import user
from Sessions import sessions
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

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

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/")
def read_root():
    return {"message": "Hello World"}

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
