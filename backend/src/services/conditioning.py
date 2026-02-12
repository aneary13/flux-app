"""Conditioning block service: protocol lookup, benchmark math, block assembly (Option II)."""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ConditioningBenchmark, ConditioningProgress, ConditioningProtocol
from src.models import ExerciseBlock


def _parse_target_modifier(modifier: str) -> tuple[str | None, float | None]:
    """Parse e.g. 'BENCHMARK_1.2' -> (benchmark_key, multiplier). Returns (None, None) if not parseable."""
    if not modifier or not modifier.strip().upper().startswith("BENCHMARK_"):
        return None, None
    match = re.match(r"BENCHMARK_([\d.]+)", modifier.strip(), re.IGNORECASE)
    if not match:
        return None, None
    try:
        mult = float(match.group(1))
        return "BENCHMARK", mult
    except ValueError:
        return None, None


async def get_conditioning_block(
    state: str,
    user_id: UUID,
    db: AsyncSession,
) -> ExerciseBlock:
    """Build the single conditioning finisher block (Option II: Service Composition).

    SS (Steady State): Only when state=RED. No levels; single free-form prescription.
    Record of SS is kept via PatternHistory (CONDITIONING:SS) and session/set data
    (duration, avg HR) for display (e.g. "last did SS 10 days ago, 20 min, 130 avg HR").

    SIT/HIIT: When GREEN/ORANGE, toggle from ConditioningProgress and use level progression.
    """
    # Step A: State check – RED always gets SS; no level tracking for SS
    progress = None
    if state == "RED":
        tier = "SS"
    else:
        stmt = select(ConditioningProgress).where(ConditioningProgress.user_id == user_id)
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        if progress is None:
            tier = "SIT"
        else:
            last_tier = progress.last_tier_performed or "NONE"
            if last_tier == "SIT":
                tier = "HIIT"
            else:
                tier = "SIT"

    # Step B: Protocol lookup – SS has a single row (level 1); SIT/HIIT use user level from progress
    if tier == "SS":
        stmt = select(ConditioningProtocol).where(
            ConditioningProtocol.tier == "SS",
            ConditioningProtocol.level == 1,
        )
    else:
        level = (progress.sit_level if tier == "SIT" else progress.hiit_level) if progress else 1
        stmt = select(ConditioningProtocol).where(
            ConditioningProtocol.tier == tier,
            ConditioningProtocol.level == level,
        )
    result = await db.execute(stmt)
    protocol = result.scalar_one_or_none()
    if protocol is None:
        description = "Zone 2 – duration by feel (e.g. 20 min)" if tier == "SS" else "8 x 30s on / 30s off"
    else:
        description = protocol.description

    # Step C: Benchmark math (SIT/HIIT only; SS has no target_modifier)
    target_suffix = ""
    if protocol and protocol.target_modifier:
        _, multiplier = _parse_target_modifier(protocol.target_modifier)
        if multiplier is not None:
            stmt = (
                select(ConditioningBenchmark)
                .where(ConditioningBenchmark.user_id == user_id)
                .order_by(ConditioningBenchmark.date.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            bench = result.scalar_one_or_none()
            if bench is not None:
                target_val = int(bench.result_metric * multiplier)
                target_suffix = f" — Target: {target_val}W"

    # Step D: Assembly
    exercise_name = description + target_suffix
    pattern = f"CONDITIONING:{tier}"

    return ExerciseBlock(
        block_type="CONDITIONING",
        exercise_name=exercise_name.strip(),
        pattern=pattern,
    )
