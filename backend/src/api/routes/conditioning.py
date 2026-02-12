"""Conditioning protocol and related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.db.seeds import seed_conditioning_protocols

router = APIRouter()


@router.post("/seed")
async def seed_conditioning(
    replace: bool = False,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Seed ConditioningProtocol table (SIT, HIIT, SS tiers from Gassed to Ready).

    Idempotent by default: no rows inserted if any protocol already exists.
    Set replace=true to clear and re-seed.

    Returns:
        Dictionary with key conditioning_protocol and count of rows inserted.
    """
    try:
        count = await seed_conditioning_protocols(db, replace=replace)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed conditioning protocols: {e!s}",
        ) from e
    return {"conditioning_protocol": count}
