"""Seed reference data for FLUX (Schema 3.0). ConditioningProtocol and exercises from config."""

from __future__ import annotations

import asyncio
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

from src.config import load_config
from src.db.models import ConditioningProtocol
from src.db.session import get_engine, get_session

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_conditioning_protocols() -> list[dict]:
    """Load protocol definitions from config.conditioning (conditioning.yaml)."""
    config = load_config(CONFIG_DIR)
    protocols = config.conditioning.protocols
    return [
        {
            "tier": p.tier,
            "level": p.level,
            "description": p.description,
            "work_duration": p.work_duration,
            "rest_duration": p.rest_duration,
            "rounds": p.rounds,
            "target_modifier": p.target_modifier,
        }
        for p in protocols
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
    protocols = load_conditioning_protocols()
    count = 0
    for row in protocols:
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
