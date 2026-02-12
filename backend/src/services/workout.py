"""Workout completion service: persist session + sets and update pattern history."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import WorkoutSessionCreate
from src.db.models import ConditioningProgress, Exercise, PatternHistory, WorkoutSession, WorkoutSet


async def _get_or_create_exercise_id(db: AsyncSession, exercise_name: str) -> int:
    """Resolve exercise name to id; create Exercise with category UNKNOWN if not found."""
    stmt = select(Exercise).where(Exercise.name == exercise_name)
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if ex:
        return ex.id
    new_ex = Exercise(
        name=exercise_name,
        category="UNKNOWN",
        modality="Unknown",
    )
    db.add(new_ex)
    await db.flush()
    return new_ex.id


async def log_completed_session(
    db: AsyncSession,
    user_id: UUID,
    payload: WorkoutSessionCreate,
) -> WorkoutSession:
    """Persist a completed workout session and update pattern history in one transaction.

    1. Ingest: Save WorkoutSession and all WorkoutSets (exercise_name resolved to exercise_id).
    2. Map: Resolve each exercise_id to pattern (Exercise.category).
    3. Update: Upsert PatternHistory so last_performed is set for each pattern.

    Unknown exercise names are auto-created in Exercise (category UNKNOWN) to preserve history.

    Args:
        db: Database session (caller commits/rolls back).
        user_id: User ID.
        payload: Validated create payload.

    Returns:
        The created WorkoutSession with sets loaded (for building response).
    """
    computed_state = payload.computed_state or "GREEN"

    session = WorkoutSession(
        user_id=user_id,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
        readiness_score=payload.readiness_score,
        computed_state=computed_state,
        session_notes=payload.session_notes,
    )
    db.add(session)
    await db.flush()

    exercise_ids_used: set[int] = set()
    for s in payload.sets:
        exercise_id = await _get_or_create_exercise_id(db, s.exercise_name)
        exercise_ids_used.add(exercise_id)
        ws = WorkoutSet(
            session_id=session.id,
            exercise_id=exercise_id,
            set_order=s.set_order,
            weight_kg=s.weight_kg,
            reps=s.reps,
            rpe=s.rpe,
            distance_meters=s.distance_meters,
            work_seconds=s.work_seconds,
            rest_seconds=s.rest_seconds,
            watts_avg=s.watts_avg,
            watts_peak=s.watts_peak,
            is_benchmark=s.is_benchmark,
            exercise_notes=s.exercise_notes,
        )
        db.add(ws)
    await db.flush()

    # Map exercise_id -> pattern (category)
    unique_ids = list(exercise_ids_used)
    stmt = select(Exercise).where(Exercise.id.in_(unique_ids))
    result = await db.execute(stmt)
    exercises = result.scalars().all()
    patterns_performed = {ex.category for ex in exercises}

    completed_at = payload.completed_at
    for pattern in patterns_performed:
        stmt = select(PatternHistory).where(
            PatternHistory.user_id == user_id,
            PatternHistory.pattern == pattern,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.last_performed = completed_at
            db.add(existing)
        else:
            ph = PatternHistory(
                user_id=user_id,
                pattern=pattern,
                last_performed=completed_at,
            )
            db.add(ph)

    if payload.conditioning_tier_performed and payload.conditioning_tier_performed in ("SIT", "HIIT", "SS"):
        tier = payload.conditioning_tier_performed
        cond_pattern = f"CONDITIONING:{tier}"
        stmt = select(PatternHistory).where(
            PatternHistory.user_id == user_id,
            PatternHistory.pattern == cond_pattern,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.last_performed = completed_at
            db.add(existing)
        else:
            db.add(PatternHistory(user_id=user_id, pattern=cond_pattern, last_performed=completed_at))

        stmt = select(ConditioningProgress).where(ConditioningProgress.user_id == user_id)
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        if progress:
            progress.last_tier_performed = tier
            progress.last_performed = completed_at
            db.add(progress)
        else:
            db.add(ConditioningProgress(user_id=user_id, last_tier_performed=tier, last_performed=completed_at))

    return session
