"""
Async SQLAlchemy engine and session factory.

Configure the Postgres/Neon connection via the DATABASE_URL environment
variable (or a .env file in the backend directory).  Accepted formats:

  postgresql://user:pass@host/db?sslmode=require
  postgresql+asyncpg://user:pass@host/db?ssl=require
  postgres://user:pass@host/db          (PaaS shorthand)
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# Load .env from the backend root directory if it exists (development convenience)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=_BACKEND_ROOT / ".env")

_raw_url: str = os.getenv("DATABASE_URL", "")


def _normalise_url(url: str) -> str:
    """Convert common Postgres URL variants to the asyncpg scheme."""
    if not url:
        return url
    # Replace shorthand postgres:// → postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg uses ?ssl=require, not ?sslmode=require
    url = re.sub(r"sslmode=require", "ssl=require", url)
    return url


DATABASE_URL: str = _normalise_url(_raw_url)

# Build engine only when DATABASE_URL is configured so the app can still
# start (and serve non-DB routes) without a database in local dev.
engine = (
    create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    if DATABASE_URL
    else None
)

AsyncSessionLocal: async_sessionmaker | None = (
    async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    if engine
    else None
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async DB session."""
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set the DATABASE_URL environment variable and restart the server."
        )
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables on startup (idempotent)."""
    if engine is None:
        return
    # Import models here so that Base.metadata is populated before create_all
    from app.db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
