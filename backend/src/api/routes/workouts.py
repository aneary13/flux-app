"""Workout recommendation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_engine, get_user_id
from src.db.models import WorkoutSession
from src.engine import WorkoutEngine
from src.models import HistoryEntry, Readiness, SessionPlan, TrainingHistory

router = APIRouter()


@router.post("/recommend", response_model=SessionPlan)
async def recommend_workout(
    readiness: Readiness,
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
    user_id: UUID = Depends(get_user_id),
) -> SessionPlan:
    """Generate workout recommendation based on readiness and history.

    Args:
        readiness: User readiness with pain and energy levels
        db: Database session
        engine: WorkoutEngine instance
        user_id: User ID from X-User-Id header

    Returns:
        SessionPlan with recommended workout details

    Raises:
        HTTPException: If no matching session is found or database operation fails
    """
    # Query WorkoutSession records for user_id, ordered by date descending
    stmt = (
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id)
        .order_by(WorkoutSession.date.desc())
    )
    result = await db.execute(stmt)
    db_sessions = result.scalars().all()

    # Convert DB records → TrainingHistory (Pydantic)
    history_entries = [
        HistoryEntry(
            archetype=session.archetype_name,
            date=session.date.date(),  # Convert datetime to date
        )
        for session in db_sessions
    ]
    history = TrainingHistory(entries=history_entries)

    # Generate session plan using engine
    try:
        session_plan = engine.generate_session(readiness, history)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return session_plan
