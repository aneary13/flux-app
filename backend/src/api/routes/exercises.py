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


def _modality_from_category(category: str) -> str:
    """Map category to Exercise.modality."""
    if category == "MOBILITY":
        return "Mobility"
    if category == "RFD":
        return "Power"
    if category == "CONDITIONING":
        return "Cardio"
    return "Strength"


@router.post("/seed")
async def seed_exercises(
    db: AsyncSession = Depends(get_db),
    engine: WorkoutEngine = Depends(get_engine),
) -> dict[str, int]:
    """Seed database with exercises from config.library.catalog.

    Uses catalog as source of truth; maps settings.unit, settings.unilateral,
    settings.load to Exercise.tracking_unit, is_unilateral, is_bodyweight.
    """
    created_count = 0
    catalog = engine.config.library.catalog

    for entry in catalog:
        if hasattr(entry, "get_settings"):
            settings = entry.get_settings()
        else:
            s = getattr(entry, "settings", None)
            settings = s if isinstance(s, dict) else (s.model_dump(exclude_none=True) if s else {})

        unit = (settings.get("unit") or "REPS").upper()
        tracking_unit = "SECS" if unit == "SECS" else ("WATTS" if unit == "WATTS" else "REPS")
        unilateral = bool(settings.get("unilateral", False))
        load = (settings.get("load") or "").upper()
        is_bodyweight = load == "BODYWEIGHT"

        stmt = select(Exercise).where(Exercise.name == entry.name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            new_exercise = Exercise(
                name=entry.name,
                category=entry.category,
                modality=_modality_from_category(entry.category),
                tracking_unit=tracking_unit,
                is_unilateral=unilateral,
                is_bodyweight=is_bodyweight,
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

    return {"created": created_count, "total_unique": len(catalog)}
