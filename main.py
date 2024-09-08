from services.db_config import setup_db
from models.UserModels import User
from dotenv import load_dotenv

load_dotenv()

engine, Session = setup_db()

