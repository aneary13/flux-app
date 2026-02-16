"""Readiness check-in endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.api.deps import get_db, get_engine, get_user_id
from src.api.schemas import ReadinessLatest
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


@router.get("/latest", response_model=ReadinessLatest)
async def get_latest_readiness(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> ReadinessLatest:
    """Return the latest daily readiness for the authenticated user.

    Returns 404 when the user has no readiness record (e.g. before first check-in).
    """
    stmt = (
        select(DailyReadiness)
        .where(DailyReadiness.user_id == user_id)
        .order_by(DailyReadiness.date.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readiness record found for this user",
        ) from None
    return ReadinessLatest(
        date=row.date,
        knee_pain=row.knee_pain,
        energy_level=row.energy_level,
        computed_state=row.computed_state,
    )
