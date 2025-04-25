from sqlalchemy import Column, Integer, String, DateTime
from src.models.base import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    salary = Column(Integer, nullable=True)