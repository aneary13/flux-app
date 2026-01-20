"""Exercise management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_engine
from src.db.models import Exercise
from src.engine import WorkoutEngine

router = APIRouter()


@router.get("/")
async def list_exercises(
    db: AsyncSession = Depends(get_db),
) -> list[Exercise]:
    """List all available exercises.

    Args:
        db: Database session

    Returns:
        List of Exercise records
    """
    stmt = select(Exercise).order_by(Exercise.name)
    result = await db.execute(stmt)
    exercises = result.scalars().all()
    return list(exercises)


@router.post("/seed")
async def seed_exercises(
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
) -> dict[str, int]:
    """Seed database with exercises from program config.

    Extracts unique exercise names from all sessions in the config
    and creates Exercise records if they don't exist.

    Args:
        db: Database session
        engine: WorkoutEngine instance

    Returns:
        Dictionary with count of exercises created

    Raises:
        HTTPException: If database operation fails
    """
    # Extract unique exercise names from all sessions
    exercise_names: set[str] = set()
    for session in engine.config.sessions:
        exercise_names.update(session.exercises)

    created_count = 0

    for exercise_name in exercise_names:
        # Check if exercise already exists
        stmt = select(Exercise).where(Exercise.name == exercise_name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            # Create new exercise with placeholder category and modality
            new_exercise = Exercise(
                name=exercise_name,
                category="General",  # Placeholder - can be enhanced later
                modality="Unknown",  # Placeholder - can be enhanced later
            )
            db.add(new_exercise)
            created_count += 1

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to seed exercises",
        ) from e

    return {"created": created_count}
