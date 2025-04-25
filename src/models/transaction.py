from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from src.models.base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime)
    amount = Column(Float)
    description = Column(String)
    category = Column(String)