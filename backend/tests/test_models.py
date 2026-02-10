"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.models import (
    ExerciseBlock,
    HistoryEntry,
    PatternConfig,
    PowerSelectionConfig,
    ProgramConfig,
    Readiness,
    SessionPlan,
    StateConfig,
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
    """Tests for configuration models."""

    def test_pattern_config(self) -> None:
        """Test PatternConfig validation."""
        patterns = PatternConfig(
            main=["SQUAT", "HINGE"],
            accessory=["LUNGE"],
            core=["CORE"],
        )
        assert len(patterns.main) == 2
        assert len(patterns.accessory) == 1
        assert len(patterns.core) == 1

    def test_power_selection_config(self) -> None:
        """Test PowerSelectionConfig validation."""
        power_selection = PowerSelectionConfig(
            GREEN="HIGH", ORANGE="LOW", RED="UPPER"
        )
        assert power_selection.GREEN == "HIGH"
        assert power_selection.ORANGE == "LOW"
        assert power_selection.RED == "UPPER"

    def test_state_config(self) -> None:
        """Test StateConfig validation."""
        state = StateConfig(name="RED", condition="knee_pain >= 6")
        assert state.name == "RED"
        assert state.condition == "knee_pain >= 6"

    def test_program_config(self) -> None:
        """Test ProgramConfig with all components."""
        from src.models import SessionStructureConfig

        patterns = PatternConfig(
            main=["SQUAT", "HINGE"],
            accessory=["LUNGE"],
            core=["CORE"],
        )
        power_selection = PowerSelectionConfig(
            GREEN="HIGH", ORANGE="LOW", RED="UPPER"
        )
        session_structure = SessionStructureConfig(
            PREP=["WARM_UP", "PATELLAR_ISO", "CORE"],
            POWER=["RFD"],
            STRENGTH=["MAIN_PATTERN"],
            ACCESSORIES=["RELATED_ACCESSORIES"],
        )
        state = StateConfig(name="RED", condition="knee_pain >= 6")

        config = ProgramConfig(
            patterns=patterns,
            pattern_priority=["SQUAT", "PUSH", "HINGE", "PULL"],
            relationships={"SQUAT": ["PULL:ACCESSORY_HORIZONTAL"]},
            library={
                "SQUAT": {
                    "MAIN": {"GREEN": "Back Squat", "ORANGE": "Tempo Goblet Squat", "RED": "SKIP"}
                }
            },
            power_selection=power_selection,
            session_structure=session_structure,
            states=[state],
        )
        assert len(config.states) == 1
        assert config.patterns.main == ["SQUAT", "HINGE"]
        assert config.power_selection.GREEN == "HIGH"
        assert config.session_structure.PREP == ["WARM_UP", "PATELLAR_ISO", "CORE"]


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
