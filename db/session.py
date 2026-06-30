import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


load_dotenv()


class Base(DeclarativeBase):
    pass


def get_db_path() -> Path:
    db_path = os.getenv("DB_PATH")

    if not db_path:
        # fallback: корень проекта / training_bot.db
        return Path(__file__).resolve().parents[1] / "tattoo_bot.db"

    return Path(db_path).resolve()


DB_PATH = get_db_path()
DB_URL = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

engine = create_async_engine(
    DB_URL,
    echo=True,
    future=True,
    poolclass=NullPool,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)