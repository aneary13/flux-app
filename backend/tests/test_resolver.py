from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from core.resolver import WorkoutResolver

# Define a clean type alias for what our fixture returns
MockBrainType = tuple[dict[str, Any], list[dict[str, Any]]]


@pytest.fixture
def mock_brain() -> MockBrainType:
    """
    Create a "mock brain" fixture so we don't need the database
    """
    configs: dict[str, Any] = {
        "logic": {
            "thresholds": {
                "knee_pain": {"lower": 3, "upper": 6},
                "energy": {"lower": 2, "upper": 5},
            },
            "pattern_priority": ["SQUAT", "PUSH", "HINGE", "PULL"],
        },
        "sessions": {},
        "selections": {},
        "conditioning": {},
    }
    # Explicitly type the empty list
    exercises: list[dict[str, Any]] = []

    return configs, exercises


def test_evaluate_state_red_pain(mock_brain: MockBrainType) -> None:
    """
    Test the triage engine when pain is red
    """
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)

    # High pain (8), Good energy (8) -> Should force RED / RECOVERY
    state, archetype = resolver._evaluate_state(knee_pain=8, energy=8)

    assert state == "RED"
    assert archetype == "RECOVERY"


def test_evaluate_state_low_energy(mock_brain: MockBrainType) -> None:
    """
    Test the triage engine when energy is red
    """
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)

    # Low pain (1), Terrible energy (2) -> Should force RED / RECOVERY
    state, archetype = resolver._evaluate_state(knee_pain=1, energy=2)

    assert state == "RED"
    assert archetype == "RECOVERY"


def test_resolve_main_pattern_tie_breaker(mock_brain: MockBrainType) -> None:
    """
    Test the UTC timestamp progression engine
    """
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)

    # We use timedelta to dynamically generate deterministic timestamps
    now = datetime.now(UTC)
    five_days_ago = (now - timedelta(days=5)).isoformat()
    two_days_ago = (now - timedelta(days=2)).isoformat()
    one_day_ago = (now - timedelta(days=1)).isoformat()

    # SQUAT and PUSH are tied at exactly 5 days elapsed
    # According to our logic.pattern_priority, SQUAT should win.
    last_trained: dict[str, str | None] = {
        "SQUAT": five_days_ago,
        "PUSH": five_days_ago,
        "HINGE": two_days_ago,
        "PULL": one_day_ago,
    }

    main_pattern = resolver._resolve_main_pattern(last_trained)

    assert main_pattern == "SQUAT"


def test_resolve_main_pattern_null_is_highest_priority(mock_brain: MockBrainType) -> None:
    """
    Test that untrained patterns are prioritised
    """
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)

    now = datetime.now(UTC)
    ten_days_ago = (now - timedelta(days=10)).isoformat()

    # Even though SQUAT hasn't been trained in 10 days, PULL has NEVER been trained (None)
    # None evaluates to infinite debt and should win
    last_trained: dict[str, str | None] = {
        "SQUAT": ten_days_ago,
        "PUSH": ten_days_ago,
        "HINGE": ten_days_ago,
        "PULL": None,
    }

    main_pattern = resolver._resolve_main_pattern(last_trained)

    assert main_pattern == "PULL"
