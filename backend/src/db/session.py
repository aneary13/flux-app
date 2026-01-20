"""Database session management for async SQLModel operations."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create async engine (will be None if DATABASE_URL is not set)
# Engine will be created lazily when needed
engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async engine.

    Raises:
        ValueError: If DATABASE_URL is not set
    """
    global engine
    if engine is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    return engine


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields an AsyncSession.

    Usage:
        async with get_session() as session:
            # Use session for database operations
            result = await session.execute(...)
            await session.commit()
    """
    db_engine = get_engine()
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables() -> None:
    """Create all database tables defined in SQLModel models.

    This function should be called once during application startup
    to ensure all tables exist. For production, use Alembic migrations instead.
    """
    db_engine = get_engine()
    async with db_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
