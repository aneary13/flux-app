"""Readiness check-in endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from src.api.deps import get_db, get_engine, get_user_id
from src.db.models import DailyReadiness
from src.engine import WorkoutEngine
from src.models import Readiness

router = APIRouter()


@router.post("/check-in")
async def check_in(
    readiness: Readiness,
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
    user_id: UUID = Depends(get_user_id),
) -> dict[str, str]:
    """Record daily readiness check-in and compute state.

    Args:
        readiness: User readiness with pain and energy levels
        db: Database session
        engine: WorkoutEngine instance
        user_id: User ID from X-User-Id header

    Returns:
        Dictionary with computed state (RED, ORANGE, or GREEN)

    Raises:
        HTTPException: If database operation fails
    """
    # Compute state using engine
    computed_state = engine.determine_state(readiness)

    # Map Readiness (Pydantic) to DailyReadiness (SQLModel)
    today = date.today()

    # Upsert logic: query for existing record
    stmt = select(DailyReadiness).where(
        DailyReadiness.user_id == user_id, DailyReadiness.date == today
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing record
        existing.knee_pain = readiness.knee_pain
        existing.energy_level = readiness.energy
        existing.computed_state = computed_state
        db.add(existing)
    else:
        # Create new record
        db_readiness = DailyReadiness(
            user_id=user_id,
            date=today,
            knee_pain=readiness.knee_pain,
            energy_level=readiness.energy,
            computed_state=computed_state,
        )
        db.add(db_readiness)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save readiness data",
        ) from e

    return {"state": computed_state}
