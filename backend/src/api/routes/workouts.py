"""Workout recommendation and completion endpoints."""

import sys
import traceback

from collections import defaultdict
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_engine, get_user_id
from src.api.schemas import WorkoutSessionCreate, WorkoutSessionRead, WorkoutSetRead
from src.db.models import Exercise, PatternHistory, WorkoutSession, WorkoutSet
from src.engine import WorkoutEngine
from src.models import HistoryEntry, Readiness, SessionPlan, TrainingHistory
from src.services.conditioning import get_conditioning_block
from src.services.workout import log_completed_session

router = APIRouter()


def _build_history_from_pattern_history(rows: list) -> TrainingHistory:
    """Build TrainingHistory from PatternHistory rows (group by date)."""
    by_date: defaultdict[date, list[str]] = defaultdict(list)
    for row in rows:
        by_date[row.last_performed.date()].append(row.pattern)
    entries = [
        HistoryEntry(impacted_patterns=patterns, date=date_)
        for date_, patterns in sorted(by_date.items(), key=lambda x: x[0], reverse=True)
    ]
    return TrainingHistory(entries=entries)


def _last_push_plane_from_history(rows: list) -> str | None:
    """From PatternHistory rows (ordered by last_performed desc), return last PUSH plane.

    Returns "VERTICAL" if last PUSH was ACCESSORY_VERTICAL, "HORIZONTAL" if ACCESSORY_HORIZONTAL, else None.
    """
    for row in rows:
        if not row.pattern.startswith("PUSH:"):
            continue
        if "ACCESSORY_VERTICAL" in row.pattern:
            return "VERTICAL"
        if "ACCESSORY_HORIZONTAL" in row.pattern:
            return "HORIZONTAL"
    return None


@router.post("/recommend", response_model=SessionPlan)
async def recommend_workout(
    readiness: Readiness,
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
    user_id: UUID = Depends(get_user_id),
) -> SessionPlan:
    """Generate workout recommendation based on readiness and pattern history.

    History is built from PatternHistory (last_performed per pattern) so that
    completing a workout resets debt for the patterns performed.
    """
    stmt = (
        select(PatternHistory)
        .where(PatternHistory.user_id == user_id)
        .order_by(PatternHistory.last_performed.desc())
    )
    result = await db.execute(stmt)
    history_rows = result.scalars().all()
    history = _build_history_from_pattern_history(history_rows)

    state = engine.determine_state(readiness)
    last_push_plane = _last_push_plane_from_history(history_rows) if state == "RED" else None

    try:
        lifting_plan = engine.generate_session(readiness, history, last_push_plane=last_push_plane)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    if state == "RED":
        return lifting_plan
    conditioning_block = await get_conditioning_block(state, user_id, db)
    blocks = list(lifting_plan.blocks) + [conditioning_block]
    return SessionPlan(session_type="GYM", blocks=blocks)


@router.post("", response_model=WorkoutSessionRead, status_code=status.HTTP_201_CREATED)
async def create_workout(
    body: WorkoutSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> WorkoutSessionRead:
    """Log a completed workout: persist session + sets and update pattern history.

    Persists all sets (micro history) and updates PatternHistory so pattern
    debt resets for the exercises performed (macro engine feedback).
    """
    try:
        session = await log_completed_session(db, user_id, body)
    except Exception as e:
        await db.rollback()
        print(f"CRITICAL ERROR: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save workout: {str(e)}")

    sets_stmt = (
        select(WorkoutSet, Exercise)
        .join(Exercise, WorkoutSet.exercise_id == Exercise.id)
        .where(WorkoutSet.session_id == session.id)
        .order_by(WorkoutSet.set_order)
    )
    sets_result = await db.execute(sets_stmt)
    rows = sets_result.all()

    return WorkoutSessionRead(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
        readiness_score=session.readiness_score,
        computed_state=session.computed_state,
        session_notes=session.session_notes,
        sets=[
            WorkoutSetRead(
                id=s.id,
                exercise_id=s.exercise_id,
                exercise_name=ex.name,
                weight_kg=s.weight_kg,
                reps=s.reps,
                rpe=s.rpe,
                set_order=s.set_order,
                distance_meters=s.distance_meters,
                work_seconds=s.work_seconds,
                rest_seconds=s.rest_seconds,
                watts_avg=s.watts_avg,
                watts_peak=s.watts_peak,
                is_benchmark=s.is_benchmark,
                exercise_notes=s.exercise_notes,
            )
            for s, ex in rows
        ],
    )
