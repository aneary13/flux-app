"""Dependency injection for FastAPI routes."""

import functools
from pathlib import Path
from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.engine import WorkoutEngine

# Path to config file relative to backend directory
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "program_config.yaml"


@functools.lru_cache(maxsize=1)
def get_engine() -> WorkoutEngine:
    """Get singleton WorkoutEngine instance.

    Uses LRU cache to ensure YAML config is only parsed once at startup.

    Returns:
        WorkoutEngine instance loaded from program_config.yaml
    """
    return WorkoutEngine(CONFIG_PATH)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an AsyncSession for database operations.

    Yields:
        AsyncSession: Database session
    """
    async with get_session() as session:
        yield session


async def get_user_id(x_user_id: Annotated[str, Header()]) -> UUID:
    """Extract user ID from X-User-Id header.

    Args:
        x_user_id: User ID from X-User-Id header

    Returns:
        UUID: Parsed user ID

    Raises:
        HTTPException: If header is missing or invalid UUID format
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header is required",
        )

    try:
        return UUID(x_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID format: {e}",
        ) from e
