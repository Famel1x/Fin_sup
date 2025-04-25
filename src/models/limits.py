from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from src.models.base import Base

class DailyLimit(Base):
    __tablename__ = "daily_limits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    recommended_limit = Column(Float)
    actual_spent = Column(Float, default=0.0)