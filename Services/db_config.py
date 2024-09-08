from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
Base = declarative_base()

def setup_db():
    engine = create_engine(f'sqlite:///{os.getenv("DB_FILE_NAME")}')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    print("Connected to database")
    return engine, Session