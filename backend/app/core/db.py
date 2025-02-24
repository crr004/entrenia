from sqlmodel import Session, create_engine, select, SQLModel
from app.models.users import User
import os

DB_URL = os.environ["POSTGRES_URL"]


def init_db():
    engine = create_engine(DB_URL)
    SQLModel.metadata.create_all(engine)
