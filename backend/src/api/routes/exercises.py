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

    Robustly scrapes exercises from config.library, handling both:
    1. Traffic Light Dicts (Squat/Hinge): {GREEN: "Name", RED: "Name"}
    2. Power Lists (RFD): ["Jump 1", "Jump 2"]

    Args:
        db: Database session
        engine: WorkoutEngine instance

    Returns:
        Dictionary with count of exercises created
    """

    def to_dict(obj):
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return vars(obj)

    # 1. Map Name -> Category to prevent duplicates
    exercises_map: dict[str, str] = {}

    # 2. Extract from Library
    # Access lowercase 'library' if 'Library' doesn't exist
    library_obj = getattr(engine.config, "library", getattr(engine.config, "Library", {}))
    library_data = to_dict(library_obj)

    for pattern, variants in library_data.items():
        # pattern = SQUAT, RFD, etc.
        if not isinstance(variants, dict):
            continue

        for variant_name, entry_data in variants.items():
            # CASE A: Standard Traffic Light Pattern (Dict)
            # Structure: {GREEN: "Back Squat", RED: "SKIP"}
            if isinstance(entry_data, dict):
                for state, exercise_name in entry_data.items():
                    if exercise_name and isinstance(exercise_name, str) and exercise_name != "SKIP":
                        if exercise_name not in exercises_map:
                            exercises_map[exercise_name] = pattern

            # CASE B: RFD/Power Pattern (List)
            # Structure: ["Hurdle Jump", "Box Jump"]
            elif isinstance(entry_data, list):
                for exercise_name in entry_data:
                    if exercise_name and isinstance(exercise_name, str):
                        if exercise_name not in exercises_map:
                            exercises_map[exercise_name] = pattern

    # 3. Check for standalone RFD section (Just in case it's not in library)
    rfd_obj = getattr(engine.config, "RFD", getattr(engine.config, "rfd", {}))
    if rfd_obj and rfd_obj != library_data.get("RFD"):
        rfd_data = to_dict(rfd_obj)
        for power_type, exercise_list in rfd_data.items():
            if isinstance(exercise_list, list):
                for exercise_name in exercise_list:
                    if exercise_name not in exercises_map:
                        exercises_map[exercise_name] = "RFD"

    # 4. Red Day: mobility_exercises (check-off) and repair_isometrics (tracked)
    mobility = getattr(engine.config, "mobility_exercises", []) or []
    for name in mobility:
        if name and name not in exercises_map:
            exercises_map[name] = "MOBILITY"
    repair_isometrics = getattr(engine.config, "repair_isometrics", []) or []
    red_metadata: dict[str, dict] = {}  # name -> {tracking_unit, is_unilateral, is_bodyweight, modality}
    for iso in repair_isometrics:
        name = getattr(iso, "name", iso.get("name") if isinstance(iso, dict) else None)
        if not name:
            continue
        if name not in exercises_map:
            exercises_map[name] = getattr(iso, "category", "ISOMETRIC")
        settings = getattr(iso, "settings", {}) if hasattr(iso, "settings") else (iso.get("settings", {}) if isinstance(iso, dict) else {})
        load_type = (settings.get("load_type") if isinstance(settings, dict) else None) or "WEIGHTED"
        red_metadata[name] = {
            "tracking_unit": "SECS",
            "is_unilateral": True,
            "is_bodyweight": load_type == "BODYWEIGHT",
            "modality": "Strength",
        }

    # 5. Database Insertion
    created_count = 0

    for exercise_name, category in exercises_map.items():
        stmt = select(Exercise).where(Exercise.name == exercise_name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            meta = red_metadata.get(exercise_name, {})
            if category == "MOBILITY":
                modality = "Mobility"
            elif category == "RFD":
                modality = "Power"
            else:
                modality = meta.get("modality") or "Strength"
            new_exercise = Exercise(
                name=exercise_name,
                category=category,
                modality=modality,
                tracking_unit=meta.get("tracking_unit", "REPS"),
                is_unilateral=meta.get("is_unilateral", False),
                is_bodyweight=meta.get("is_bodyweight", False),
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
