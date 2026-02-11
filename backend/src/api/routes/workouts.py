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
from src.db.models import PatternInventory, WorkoutSession, WorkoutSet
from src.engine import WorkoutEngine
from src.models import HistoryEntry, Readiness, SessionPlan, TrainingHistory
from src.services.workout import log_completed_session

router = APIRouter()


def _build_history_from_inventory(inventory_rows: list) -> TrainingHistory:
    """Build TrainingHistory from PatternInventory rows (group by date)."""
    by_date: defaultdict[date, list[str]] = defaultdict(list)
    for row in inventory_rows:
        by_date[row.last_performed.date()].append(row.pattern)
    entries = [
        HistoryEntry(impacted_patterns=patterns, date=date_)
        for date_, patterns in sorted(by_date.items(), key=lambda x: x[0], reverse=True)
    ]
    return TrainingHistory(entries=entries)


@router.post("/recommend", response_model=SessionPlan)
async def recommend_workout(
    readiness: Readiness,
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
    user_id: UUID = Depends(get_user_id),
) -> SessionPlan:
    """Generate workout recommendation based on readiness and pattern inventory.

    History is built from PatternInventory (last_performed per pattern) so that
    completing a workout resets debt for the patterns performed.
    """
    stmt = (
        select(PatternInventory)
        .where(PatternInventory.user_id == user_id)
        .order_by(PatternInventory.last_performed.desc())
    )
    result = await db.execute(stmt)
    inventory_rows = result.scalars().all()
    history = _build_history_from_inventory(inventory_rows)

    try:
        session_plan = engine.generate_session(readiness, history)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return session_plan


@router.post("", response_model=WorkoutSessionRead, status_code=status.HTTP_201_CREATED)
async def create_workout(
    body: WorkoutSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> WorkoutSessionRead:
    """Log a completed workout: persist session + sets and update pattern inventory.

    Persists all sets (micro history) and updates PatternInventory so pattern
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
        select(WorkoutSet)
        .where(WorkoutSet.session_id == session.id)
        .order_by(WorkoutSet.set_order)
    )
    sets_result = await db.execute(sets_stmt)
    sets = sets_result.scalars().all()

    return WorkoutSessionRead(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
        readiness_score=session.readiness_score,
        notes=session.notes,
        sets=[
            WorkoutSetRead(
                id=s.id,
                exercise_name=s.exercise_name,
                weight_kg=s.weight_kg,
                reps=s.reps,
                rpe=s.rpe,
                set_order=s.set_order,
            )
            for s in sets
        ],
    )
