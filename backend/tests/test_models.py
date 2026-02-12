"""Tests for Pydantic models (input/output and config)."""

import pytest
from pydantic import ValidationError

from src.models import (
    ExerciseBlock,
    HistoryEntry,
    Readiness,
    SessionPlan,
    TrainingHistory,
)


class TestReadiness:
    """Tests for Readiness model."""

    def test_valid_readiness(self) -> None:
        """Test valid readiness values."""
        readiness = Readiness(knee_pain=5, energy=7)
        assert readiness.knee_pain == 5
        assert readiness.energy == 7

    def test_readiness_boundary_values(self) -> None:
        """Test boundary values (0 and 10)."""
        readiness_min = Readiness(knee_pain=0, energy=0)
        assert readiness_min.knee_pain == 0
        assert readiness_min.energy == 0

        readiness_max = Readiness(knee_pain=10, energy=10)
        assert readiness_max.knee_pain == 10
        assert readiness_max.energy == 10

    def test_readiness_invalid_range(self) -> None:
        """Test invalid range values."""
        with pytest.raises(ValidationError):
            Readiness(knee_pain=11, energy=5)

        with pytest.raises(ValidationError):
            Readiness(knee_pain=5, energy=-1)

    def test_readiness_missing_fields(self) -> None:
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            Readiness(knee_pain=5)  # type: ignore


class TestTrainingHistory:
    """Tests for TrainingHistory model."""

    def test_empty_history(self) -> None:
        """Test empty training history."""
        history = TrainingHistory()
        assert history.entries == []

    def test_history_with_entries(self) -> None:
        """Test history with entries."""
        from datetime import date

        entry1 = HistoryEntry(
            impacted_patterns=["SQUAT", "PULL_HORIZ"], date=date(2024, 1, 1)
        )
        entry2 = HistoryEntry(impacted_patterns=["HINGE"], date=date(2024, 1, 3))
        history = TrainingHistory(entries=[entry1, entry2])
        assert len(history.entries) == 2


class TestConfigModels:
    """Tests for modular config (src.config)."""

    def test_logic_config_patterns(self) -> None:
        """Test LogicConfig.PatternsConfig."""
        from src.config import LogicConfig, PatternsConfig

        patterns = PatternsConfig(
            main=["SQUAT", "HINGE"],
            accessory=["LUNGE"],
            core=["CORE"],
        )
        assert patterns.main == ["SQUAT", "HINGE"]
        assert patterns.accessory == ["LUNGE"]
        assert patterns.core == ["CORE"]

    def test_logic_config_power_selection(self) -> None:
        """Test LogicConfig.PowerSelectionConfig."""
        from src.config import PowerSelectionConfig

        ps = PowerSelectionConfig(GREEN="HIGH", ORANGE="LOW", RED="UPPER")
        assert ps.GREEN == "HIGH"
        assert ps.ORANGE == "LOW"
        assert ps.RED == "UPPER"

    def test_load_config(self) -> None:
        """Test load_config returns ProgramConfig with library, logic, sessions, selections, conditioning."""
        from pathlib import Path

        from src.config import load_config

        # Use repo config dir
        config_dir = Path(__file__).resolve().parent.parent / "config"
        config = load_config(config_dir)
        assert config.logic.pattern_priority
        assert config.logic.patterns.main
        assert config.selections
        assert hasattr(config.sessions, "GYM")
        assert hasattr(config.sessions, "RECOVERY")
        assert config.library.catalog is not None
        assert config.conditioning.protocols is not None


class TestSessionPlan:
    """Tests for SessionPlan output model."""

    def test_session_plan(self) -> None:
        """Test SessionPlan creation with blocks."""
        blocks = [
            ExerciseBlock(
                block_type="PREP", exercise_name="Patellar Isometric", pattern=None
            ),
            ExerciseBlock(
                block_type="POWER", exercise_name="Depth Jumps", pattern=None
            ),
            ExerciseBlock(
                block_type="MAIN", exercise_name="Back Squat", pattern="SQUAT"
            ),
            ExerciseBlock(
                block_type="ACCESSORY_1",
                exercise_name="Cable Row",
                pattern="PULL_HORIZ",
            ),
        ]
        plan = SessionPlan(session_type="GYM", blocks=blocks)

        assert plan.session_type == "GYM"
        assert plan.archetype == "GYM"  # Computed field
        assert plan.session_name == "GYM: Back Squat"  # Computed field
        assert len(plan.exercises) == 4  # Computed field
        assert "Back Squat" in plan.exercises
        assert plan.priority_score == 0.0  # Default value

    def test_session_plan_computed_fields(self) -> None:
        """Test that computed fields work correctly."""
        blocks = [
            ExerciseBlock(
                block_type="MAIN", exercise_name="Bench Press", pattern="PUSH"
            )
        ]
        plan = SessionPlan(session_type="GYM", blocks=blocks)

        # Verify computed fields are accessible
        assert plan.exercises == ["Bench Press"]
        assert plan.session_name == "GYM: Bench Press"
        assert plan.archetype == "GYM"
