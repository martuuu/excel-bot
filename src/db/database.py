from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///fifa_bot.db")

# Crear engine asincrónico para SQLite
engine = create_async_engine(DATABASE_URL, echo=False)

# Creador de sesiones asincrónicas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()

async def init_db():
    """Initializes the database by creating all tables if they don't exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
