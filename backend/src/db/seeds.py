"""Seed reference data for FLUX (Schema 3.0). ConditioningProtocol from Gassed to Ready logic."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure backend src is on path when run as script
if __name__ == "__main__":
    backend = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(backend))

from dotenv import load_dotenv
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.db.models import ConditioningProtocol
from src.db.session import get_engine, get_session


# Gassed to Ready: SIT and HIIT have levels 1–8; SS is free-form (no levels), only when state=RED.
CONDITIONING_PROTOCOLS = [
    # SIT (Sprint Interval Training) – short max efforts, long rest
    {"tier": "SIT", "level": 1, "description": "4 x 10s max / 90s rest", "work_duration": 10, "rest_duration": 90, "rounds": 4, "target_modifier": None},
    {"tier": "SIT", "level": 2, "description": "5 x 10s max / 90s rest", "work_duration": 10, "rest_duration": 90, "rounds": 5, "target_modifier": None},
    {"tier": "SIT", "level": 3, "description": "6 x 10s max / 90s rest", "work_duration": 10, "rest_duration": 90, "rounds": 6, "target_modifier": None},
    {"tier": "SIT", "level": 4, "description": "6 x 15s max / 2 min rest", "work_duration": 15, "rest_duration": 120, "rounds": 6, "target_modifier": None},
    {"tier": "SIT", "level": 5, "description": "7 x 15s max / 2 min rest", "work_duration": 15, "rest_duration": 120, "rounds": 7, "target_modifier": None},
    {"tier": "SIT", "level": 6, "description": "8 x 15s max / 2 min rest", "work_duration": 15, "rest_duration": 120, "rounds": 8, "target_modifier": None},
    {"tier": "SIT", "level": 7, "description": "6 x 20s max / 2 min rest", "work_duration": 20, "rest_duration": 120, "rounds": 6, "target_modifier": None},
    {"tier": "SIT", "level": 8, "description": "8 x 20s max / 2 min rest", "work_duration": 20, "rest_duration": 120, "rounds": 8, "target_modifier": None},
    # HIIT – 30s on / 30s off style
    {"tier": "HIIT", "level": 1, "description": "6 x 30s on / 30s off", "work_duration": 30, "rest_duration": 30, "rounds": 6, "target_modifier": None},
    {"tier": "HIIT", "level": 2, "description": "8 x 30s on / 30s off", "work_duration": 30, "rest_duration": 30, "rounds": 8, "target_modifier": "BENCHMARK_1.2"},
    {"tier": "HIIT", "level": 3, "description": "10 x 30s on / 30s off", "work_duration": 30, "rest_duration": 30, "rounds": 10, "target_modifier": "BENCHMARK_1.2"},
    {"tier": "HIIT", "level": 4, "description": "8 x 45s on / 45s off", "work_duration": 45, "rest_duration": 45, "rounds": 8, "target_modifier": "BENCHMARK_1.2"},
    {"tier": "HIIT", "level": 5, "description": "10 x 45s on / 45s off", "work_duration": 45, "rest_duration": 45, "rounds": 10, "target_modifier": "BENCHMARK_1.2"},
    {"tier": "HIIT", "level": 6, "description": "8 x 60s on / 60s off", "work_duration": 60, "rest_duration": 60, "rounds": 8, "target_modifier": "BENCHMARK_1.2"},
    {"tier": "HIIT", "level": 7, "description": "10 x 60s on / 60s off", "work_duration": 60, "rest_duration": 60, "rounds": 10, "target_modifier": "BENCHMARK_1.2"},
    {"tier": "HIIT", "level": 8, "description": "12 x 60s on / 60s off", "work_duration": 60, "rest_duration": 60, "rounds": 12, "target_modifier": "BENCHMARK_1.2"},
    # SS (Steady State) – Zone 2, only when state=RED. No levels; duration by feel. Record kept for display (e.g. "last SS 10 days ago, 20 min, 130 avg HR" from session/set data).
    {"tier": "SS", "level": 1, "description": "Zone 2 – duration by feel (e.g. 20 min)", "work_duration": None, "rest_duration": None, "rounds": 1, "target_modifier": None},
]


async def seed_conditioning_protocols(db: AsyncSession, replace: bool = False) -> int:
    """Insert ConditioningProtocol rows. If replace=True, delete existing first. Returns count inserted."""
    if replace:
        await db.execute(delete(ConditioningProtocol))
        await db.flush()
    else:
        existing = await db.execute(select(ConditioningProtocol).limit(1))
        if existing.scalar_one_or_none() is not None:
            return 0
    count = 0
    for row in CONDITIONING_PROTOCOLS:
        proto = ConditioningProtocol(**row)
        db.add(proto)
        count += 1
    await db.flush()
    return count


async def run_seeds(replace_protocols: bool = False) -> dict[str, int]:
    """Run all seeds. Returns dict of table name -> rows added."""
    get_engine()
    result: dict[str, int] = {}
    async with get_session() as session:
        result["conditioning_protocol"] = await seed_conditioning_protocols(session, replace=replace_protocols)
    return result


def main() -> None:
    """CLI: run from backend dir with `uv run python -m src.db.seeds` or `python src/db/seeds.py`."""
    replace = "--replace" in sys.argv or "-r" in sys.argv
    counts = asyncio.run(run_seeds(replace_protocols=replace))
    print("Seeds run:", counts)
    for name, n in counts.items():
        if n:
            print(f"  {name}: {n} rows")


if __name__ == "__main__":
    main()
