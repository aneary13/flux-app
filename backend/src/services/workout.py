"""Workout completion service: persist session + sets and update pattern inventory."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import WorkoutSessionCreate
from src.db.models import Exercise, PatternInventory, WorkoutSession, WorkoutSet


async def log_completed_session(
    db: AsyncSession,
    user_id: UUID,
    payload: WorkoutSessionCreate,
) -> WorkoutSession:
    """Persist a completed workout session and update pattern inventory in one transaction.

    Datetimes from the payload are timezone-aware and stored as TIMESTAMPTZ (UTC) in the DB;
    they are passed through without stripping timezone info.

    1. Ingest: Save WorkoutSession and all WorkoutSets.
    2. Map: Resolve each unique exercise_name to a pattern (Exercise.category).
    3. Update: Upsert PatternInventory so last_performed is set for each pattern.

    Unknown exercise names are skipped for pattern update (sets are still stored).

    Args:
        db: Database session (caller commits/rolls back).
        user_id: User ID.
        payload: Validated create payload.

    Returns:
        The created WorkoutSession with sets loaded (for building response).
    """
    # 1. Ingest
    session = WorkoutSession(
        user_id=user_id,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
        readiness_score=payload.readiness_score,
        notes=payload.notes,
    )
    db.add(session)
    await db.flush()

    for s in payload.sets:
        ws = WorkoutSet(
            session_id=session.id,
            exercise_name=s.exercise_name,
            weight_kg=s.weight_kg,
            reps=s.reps,
            rpe=s.rpe,
            set_order=s.set_order,
        )
        db.add(ws)
    await db.flush()

    # 2. Map: exercise_name -> pattern (category)
    unique_names = list({s.exercise_name for s in payload.sets})
    stmt = select(Exercise).where(Exercise.name.in_(unique_names))
    result = await db.execute(stmt)
    exercises = result.scalars().all()
    patterns_performed = {ex.category for ex in exercises}

    # 3. Update PatternInventory
    completed_at = payload.completed_at
    for pattern in patterns_performed:
        stmt = select(PatternInventory).where(
            PatternInventory.user_id == user_id,
            PatternInventory.pattern == pattern,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.last_performed = completed_at
            db.add(existing)
        else:
            inv = PatternInventory(
                user_id=user_id,
                pattern=pattern,
                last_performed=completed_at,
            )
            db.add(inv)

    return session
