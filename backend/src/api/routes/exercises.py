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
    """List all available exercises."""
    stmt = select(Exercise).order_by(Exercise.name)
    result = await db.execute(stmt)
    exercises = result.scalars().all()
    return list(exercises)


@router.post("/seed")
async def seed_exercises(
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
) -> dict[str, int]:
    """Seed database with exercises from Phase 6 V2 Config.

    Scrapes exercises from:
    1. config.library (Patterns -> Variants -> Traffic Lights)
    2. config.RFD (Power categories)

    Args:
        db: Database session
        engine: WorkoutEngine instance

    Returns:
        Dictionary with count of exercises created
    """
    
    # 1. Helper to handle Pydantic Models vs Dicts safely
    def to_dict(obj):
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return vars(obj)

    # Dictionary to map Name -> Category (e.g., "Back Squat" -> "SQUAT")
    # Using a dict automatically handles deduplication
    exercises_map: dict[str, str] = {}

    # 2. Extract from Library (Strength, Core, Iso)
    # Access lowercase 'library' if 'Library' doesn't exist (Pydantic convention)
    library_obj = getattr(engine.config, "library", getattr(engine.config, "Library", {}))
    library_data = to_dict(library_obj)

    for pattern, variants in library_data.items():
        # pattern = SQUAT, HINGE, etc.
        for variant_name, states in variants.items():
            # states = {GREEN: "...", RED: "..."}
            for state, exercise_name in states.items():
                if exercise_name and exercise_name != "SKIP":
                    # Only add if not present (First category wins)
                    if exercise_name not in exercises_map:
                        exercises_map[exercise_name] = pattern

    # 3. Extract from RFD (Power)
    # Check for 'RFD' (YAML exact match) or 'rfd' (Python lowercase)
    rfd_obj = getattr(engine.config, "RFD", getattr(engine.config, "rfd", {}))
    rfd_data = to_dict(rfd_obj)

    for power_type, exercise_list in rfd_data.items():
        # exercise_list = ["Hurdle Jump", "Hang Power Clean"]
        for exercise_name in exercise_list:
            if exercise_name not in exercises_map:
                exercises_map[exercise_name] = "RFD"

    # 4. Database Insertion
    created_count = 0

    for exercise_name, category in exercises_map.items():
        # Check if exercise already exists
        stmt = select(Exercise).where(Exercise.name == exercise_name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            new_exercise = Exercise(
                name=exercise_name,
                category=category,  # Now uses 'SQUAT', 'RFD', 'CORE' etc.
                modality="Strength" if category != "RFD" else "Power",
            )
            db.add(new_exercise)
            created_count += 1

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed exercises: {str(e)}",
        ) from e

    return {"created": created_count, "total_unique": len(exercises_map)}
    