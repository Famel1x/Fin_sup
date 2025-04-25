from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src import models
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from loguru import logger

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./budgetbot.db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def init_db(app=None):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("База данных (SQLite) инициализирована ✅")
    yield
    # optionally: teardown logic